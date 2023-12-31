#! /usr/bin/env python3
import argparse
import json
import logging
import logging.config
import os
import sys
import time
import nltk
from nltk.stem import *
from nltk.corpus import wordnet as wn, brown
from nltk import word_tokenize, pos_tag
from collections import defaultdict
from concurrent import futures

# Add Generated folder to module path.
PARENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(PARENT_DIR, 'generated'))

import ServerSideExtension_pb2 as SSE
import grpc
from scripteval import ScriptEval
from ssedata import FunctionType
from Xmr_functions import generateDataSet

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
_MINFLOAT = float('-inf')


class ExtensionService(SSE.ConnectorServicer):
    """
    A simple SSE-plugin created for the Column Operations example.
    """

    def __init__(self, funcdef_file):
        """
        Class initializer.
        :param funcdef_file: a function definition JSON file
        """

        self._function_definitions = funcdef_file
        self.scriptEval = ScriptEval()
        os.makedirs('logs', exist_ok=True)
        log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logger.config')
        logging.config.fileConfig(log_file)
        logging.info('Logging enabled')
        ## section for downloads etc to only run on startup
        nltk.download('brown')

    @property
    def function_definitions(self):
        """
        :return: json file with function definitions
        """
        return self._function_definitions

    @property
    def functions(self):
        """
        :return: Mapping of function id and implementation
        """
        return {            
            0: '_PorterStem',
            1: '_Lemma',
            2: '_XMR_row',
            3: '_XMR_table',
            4: '_PorterStem_table',
            5: '_Rev_Stem_table'
        }

    """
    Implementation of added functions.
    """
    @staticmethod
    def _Rev_Stem_table(request, context):
      
        """
        stem a single word.
        :param request: iterable sequence of bundled rows
        :return: string
        """
        table = SSE.TableDescription(name='Porter_Table')
        table.fields.add(name='Original', dataType=SSE.STRING)
        table.fields.add(name='Stemmed', dataType=SSE.STRING)
        md = (('qlik-tabledescription-bin', table.SerializeToString()),('qlik-cache', 'no-store'))
        context.send_initial_metadata(md)
      
        stemmer = PorterStemmer()
        
        wordlist_lowercased = set(i.lower() for i in brown.words())
        #print (wordlist_lowercased)
        # Iterate total words
        response_rows =[]
        for word in wordlist_lowercased:
           
            param = stemmer.stem(word)
            orig = word
            duals = iter([SSE.Dual(strData=orig),SSE.Dual(strData=param)])
            response_rows.append(SSE.Row(duals=duals))
            # params.append(param)
        yield SSE.BundledRows(rows=response_rows)

    @staticmethod
    def _PorterStem_table(request, context):
      
        """
        stem a table of single words, using load * extension in script.
        :param request: iterable sequence of bundled rows
        :return: string
        """
        table = SSE.TableDescription(name='Porter_Table')
        table.fields.add(name='Original', dataType=SSE.STRING)
        table.fields.add(name='Stemmed', dataType=SSE.STRING)
        md = (('qlik-tabledescription-bin', table.SerializeToString()),('qlik-cache', 'no-store'))
        context.send_initial_metadata(md)
      
        stemmer = PorterStemmer()


        # Iterate over bundled rows
        for request_rows in request:
            # Iterate over rows
            #print(request_rows)
            response_rows =[]
            for row in request_rows.rows:
                #print (row)
                # Retrieve string value of parameter and append to the params variable
                # Length of param is 1 since one column is received, the [0] collects the first value in the list
                param = [stemmer.stem(d.strData) for d in row.duals][0]
                orig = [x.strData for x in row.duals][0]
                duals = iter([SSE.Dual(strData=orig),SSE.Dual(strData=param)])
                response_rows.append(SSE.Row(duals=duals))
                # params.append(param)
        yield SSE.BundledRows(rows=response_rows)




    @staticmethod
    def _XMR_table(request, context):
        table = SSE.TableDescription(name='XMR_Table')
        table.fields.add(name='Dimension', dataType=SSE.NUMERIC)
        table.fields.add(name='Measure', dataType=SSE.NUMERIC)
        table.fields.add(name='UCL', dataType=SSE.NUMERIC)
        table.fields.add(name='LCL', dataType=SSE.NUMERIC)
        table.fields.add(name='MR', dataType=SSE.NUMERIC)
        table.fields.add(name='Mean', dataType=SSE.NUMERIC)
        table.fields.add(name='highlight', dataType=SSE.NUMERIC)
        md = (('qlik-tabledescription-bin', table.SerializeToString()),('qlik-cache', 'no-store'))
        context.send_initial_metadata(md)
        #md = (('qlik-cache', 'no-store'),)
        #context.send_initial_metadata(md)
        counter = 0
        #print(request)
        # Iterate over bundled rows
        for request_rows in request:
            num_array = []
            # Iterating over rows
           
            for row in request_rows.rows:
                #print(row)
                num_array.append({"dim":[d.numData for d in row.duals][0], "value":[d.numData for d in row.duals][2],"reCalcID" : [d.strData for d in row.duals][1],"counter": counter })
                counter= counter+1
        #print(num_array)  
        xmrcalcs = sorted(generateDataSet(num_array),key=lambda x:x['counter'])
        #print(xmrcalcs)

        

        response_rows = []
        for x in xmrcalcs:
            UCL = x['currUCL']
            LCL = x['currLCL']
            dim = x['dim']
            val = x['value']
            MR = x['MR']
            AVG = x['currAvg']
            high = x['highlight']
            #print(result)
            #print(x["counter"])
            duals = iter([SSE.Dual(numData=dim,strData=str(dim)),SSE.Dual(numData=val,strData=str(val)),SSE.Dual(numData=UCL,strData=str(UCL)), SSE.Dual(numData=LCL,strData=str(LCL)), SSE.Dual(numData=MR,strData=str(MR)), SSE.Dual(numData=AVG,strData=str(AVG)), SSE.Dual(numData=high,strData=str(high))])
            response_rows.append(SSE.Row(duals=duals))

        yield SSE.BundledRows(rows=response_rows)


    @staticmethod
    def _XMR_row(request, context):
        md = (('qlik-cache', 'no-store'),)
        context.send_initial_metadata(md)
        counter = 0
        #print(request)
        # Iterate over bundled rows
        for request_rows in request:
            num_array = []
            # Iterating over rows
           
            for row in request_rows.rows:
                dataType = [d.strData for d in row.duals][0]
                num_array.append({"dim":[d.numData for d in row.duals][1], "value":[d.numData for d in row.duals][2],"reCalcID" : [d.strData for d in row.duals][3],"counter": counter })
                counter= counter+1
          
        xmrcalcs = sorted(generateDataSet(num_array),key=lambda x:x['counter'])
        #print(xmrcalcs)
        if dataType == 'UCL':
            item = 'currUCL'
        elif dataType == 'LCL':
            item = 'currLCL'
        elif dataType == 'MR':
            item = 'MR'
        elif dataType == 'highlight':
            item = 'highlight'
        elif dataType == 'AVG':
            item = 'currAvg'
        

        response_rows = []
        for x in xmrcalcs:
            result = x[item]
            #print(result)
            #print(x["counter"])
            duals = iter([SSE.Dual(numData=result)])
            response_rows.append(SSE.Row(duals=duals))

        yield SSE.BundledRows(rows=response_rows)


  
    @staticmethod
    def _PorterStem(request, context):
      
        """
        stem a single word.
        :param request: iterable sequence of bundled rows
        :return: string
        """
      
        stemmer = PorterStemmer()


        # Iterate over bundled rows
        for request_rows in request:
            # Iterate over rows
            response_rows =[]
            for row in request_rows.rows:
                # Retrieve string value of parameter and append to the params variable
                # Length of param is 1 since one column is received, the [0] collects the first value in the list
                param = [stemmer.stem(d.strData) for d in row.duals][0]
                duals = iter([SSE.Dual(strData=param)])
                response_rows.append(SSE.Row(duals=duals))
                # params.append(param)
        yield SSE.BundledRows(rows=response_rows)


    @staticmethod
    def _Lemma(request, context):
      
        """
        obtain wordnet lemma from a single word.
        :param request: iterable sequence of bundled rows
        :return: string
        """
        nltk.download('averaged_perceptron_tagger')
        tag_map = defaultdict(lambda : wn.NOUN)
        tag_map['J'] = wn.ADJ
        tag_map['V'] = wn.VERB
        tag_map['R'] = wn.ADV

        print(tag_map)
        lemma_function = WordNetLemmatizer()

        # Iterate over bundled rows
        for request_rows in request:
            # Iterate over rows
            response_rows =[]
            for row in request_rows.rows:
                # Retrieve string value of parameter and append to the params variable
                # Length of param is 1 since one column is received, the [0] collects the first value in the list
                
                print(row.duals[0].strData)
                #Ptag = nltk.pos_tag(row.duals[0].strData)#[0][1]
                #Tag = tag_map.get(Ptag,"n")
                lemma = lemma_function.lemmatize(row.duals[0].strData,'v')
                duals = iter([SSE.Dual(strData=lemma)])
                response_rows.append(SSE.Row(duals=duals))
                # params.append(param)
        yield SSE.BundledRows(rows=response_rows)
        # Aggregate parameters to a single string
        # result = ', '.join(params)
        # result = params

        # Create an iterable of dual with the result
        # duals = iter([SSE.Dual(strData=params)])

        # Yield the row data as bundled rows
        # yield params # SSE.BundledRows(rows=[SSE.Row(duals=duals)])

    @staticmethod
    def _get_function_id(context):
        """
        Retrieve function id from header.
        :param context: context
        :return: function id
        """
        metadata = dict(context.invocation_metadata())
        header = SSE.FunctionRequestHeader()
        header.ParseFromString(metadata['qlik-functionrequestheader-bin'])

        return header.functionId

    """
    Implementation of rpc functions.
    """

    def GetCapabilities(self, request, context):
        """
        Get capabilities.
        Note that either request or context is used in the implementation of this method, but still added as
        parameters. The reason is that gRPC always sends both when making a function call and therefore we must include
        them to avoid error messages regarding too many parameters provided from the client.
        :param request: the request, not used in this method.
        :param context: the context, not used in this method.
        :return: the capabilities.
        """
        logging.info('GetCapabilities')

        # Create an instance of the Capabilities grpc message
        # Enable(or disable) script evaluation
        # Set values for pluginIdentifier and pluginVersion
        capabilities = SSE.Capabilities(allowScript=False,
                                        pluginIdentifier='UHMB PythonConnector - Qlik',
                                        pluginVersion='v1.1.0')

        # If user defined functions supported, add the definitions to the message
        with open(self.function_definitions) as json_file:
            # Iterate over each function definition and add data to the Capabilities grpc message
            for definition in json.load(json_file)['Functions']:
                function = capabilities.functions.add()
                function.name = definition['Name']
                function.functionId = definition['Id']
                function.functionType = definition['Type']
                function.returnType = definition['ReturnType']

                # Retrieve name and type of each parameter
                for param_name, param_type in sorted(definition['Params'].items()):
                    function.params.add(name=param_name, dataType=param_type)

                logging.info('Adding to capabilities: {}({})'.format(function.name,
                                                                     [p.name for p in function.params]))

        return capabilities

    def ExecuteFunction(self, request_iterator, context):
        """
        Call corresponding function based on function id sent in header.
        :param request_iterator: an iterable sequence of RowData.
        :param context: the context.
        :return: an iterable sequence of RowData.
        """
        # Retrieve function id
        func_id = self._get_function_id(context)
        logging.info('ExecuteFunction (functionId: {})'.format(func_id))

        return getattr(self, self.functions[func_id])(request_iterator, context)

    def EvaluateScript(self, request, context):
        """
        Support script evaluation, based on different function and data types.
        :param request:
        :param context:
        :return:
        """
        # Retrieve header from request
        metadata = dict(context.invocation_metadata())
        header = SSE.ScriptRequestHeader()
        header.ParseFromString(metadata['qlik-scriptrequestheader-bin'])

        # Retrieve function type
        func_type = self.scriptEval.get_func_type(header)

        # Verify function type
        if (func_type == FunctionType.Tensor) or (func_type == FunctionType.Aggregation):
            return self.scriptEval.EvaluateScript(request, context, header, func_type)
        else:
            # This plugin does not support other function types than tensor and aggregation.
            # Make sure the error handling, including logging, works as intended in the client
            msg = 'Function type {} is not supported in this plugin.'.format(func_type.name)
            context.set_code(grpc.StatusCode.UNIMPLEMENTED)
            context.set_details(msg)
            # Raise error on the plugin-side
            raise grpc.RpcError(grpc.StatusCode.UNIMPLEMENTED, msg)

    """
    Implementation of the Server connecting to gRPC.
    """

    def Serve(self, port, pem_dir):
        """
        Server
        :param port: port to listen on.
        :param pem_dir: Directory including certificates
        :return: None
        """
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        SSE.add_ConnectorServicer_to_server(self, server)

        if pem_dir:
            # Secure connection
            with open(os.path.join(pem_dir, 'sse_server_key.pem'), 'rb') as f:
                private_key = f.read()
            with open(os.path.join(pem_dir, 'sse_server_cert.pem'), 'rb') as f:
                cert_chain = f.read()
            with open(os.path.join(pem_dir, 'root_cert.pem'), 'rb') as f:
                root_cert = f.read()
            credentials = grpc.ssl_server_credentials([(private_key, cert_chain)], root_cert, True)
            server.add_secure_port('[::]:{}'.format(port), credentials)
            logging.info('*** Running server in secure mode on port: {} ***'.format(port))
        else:
            # Insecure connection
            server.add_insecure_port('[::]:{}'.format(port))
            logging.info('*** Running server in insecure mode on port: {} ***'.format(port))

        server.start()
        try:
            while True:
                time.sleep(_ONE_DAY_IN_SECONDS)
        except KeyboardInterrupt:
            server.stop(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', nargs='?', default='50060')
    parser.add_argument('--pem_dir', nargs='?')
    parser.add_argument('--definition_file', nargs='?', default='functions.json')
    args = parser.parse_args()

    # need to locate the file when script is called from outside it's location dir.
    def_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.definition_file)

    calc = ExtensionService(def_file)
    calc.Serve(args.port, args.pem_dir)
