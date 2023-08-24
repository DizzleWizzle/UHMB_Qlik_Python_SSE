import ServerSideExtension_pb2 as SSE
import datetime

def generateDataSet(data,runlength=7 ,trendlength =7,clunderzero =1,calcpoints=200,within1sigma=15,useBaseline =False):
    optSD =3
    unique = list(dict.fromkeys([item['reCalcID'] for item in data]))
    Holding = []
    newdata = []
    for ID in unique:
        temp = sorted([x for x in data if x['reCalcID'] == ID],key=lambda x:x['dim'])
    
        Holding.append(temp)
        temp = None
    for group in Holding:
        trimmed = group.copy()
        if len(trimmed) >= calcpoints and calcpoints > 0 and useBaseline == True:
            trimmed = trimmed[:calcpoints]
        trimmed[0]['MR'] = 0
        for i in range(1, len(trimmed)):
            trimmed[i]['MR'] = abs(trimmed[i]['value'] - trimmed[i-1]['value'])
        xAvg = sum([d['value'] for d in trimmed]) / len(trimmed)
        xMR = sum([d['MR'] for d in trimmed]) / (len(trimmed)-1)
        xUCL = (xMR / 1.128 * optSD) + xAvg
        xLCL = xAvg - (xMR / 1.128 * optSD)
        if clunderzero == False:
            if xLCL < 0:
                xLCL = 0
        xSigma = xMR / 1.128
        for row in group:
            row['currAvg'] = xAvg
            row['currUCL'] = xUCL
            row['currLCL'] = xLCL
            row['currSigma'] = xSigma
        newdata.extend(group)

    data = sorted(newdata ,key=lambda x:x['dim'])
    newdata = []


    for i in range(len(data)):
        d = data[i]
        #d['dim'] = dateFromQlikNumber(d['dim'])
        # d['value'] = d['value']
        #if i > 0:
        #    d['MR'] = d['value'] - data[i - 1]['value']
        meansum = meanSumCheck(data, i, runlength)
        revmeansum = revMeanSumCheck(data, i, runlength)
        trendsum = trendSumCheck(data, i, trendlength - 1)
        closetomean = closeToMean(data, i, within1sigma)
        data = nearUCLCheck(data, i, 3)
        data = nearLCLCheck(data, i, 3)
        

        d = data[i]
        d.setdefault('nearUCLCheck',0)
        d.setdefault('nearLCLCheck',0)
        if meansum == runlength or revmeansum == runlength or ((i > 0) and (data[i - 1]['check'] == 1 and d['value'] > d['currAvg'])):
                d['check'] = 1
        elif meansum == -runlength or revmeansum == -runlength or ((i > 0) and (data[i - 1]['check'] == -1 and d['value'] < d['currAvg'])):
            d['check'] = -1
        else:
            d['check'] = 0

        if trendsum >= (trendlength - 1) or ((i > 0) and (data[i - 1]['asctrendcheck'] == 1 and d['value'] > data[i - 1]['value'])):
            d['asctrendcheck'] = 1
        else:
            d['asctrendcheck'] = 0

        if trendsum <= -1 * (trendlength - 1) or ((i > 0) and (data[i - 1]['desctrendcheck'] == 1 and d['value'] < data[i - 1]['value'])):
            d['desctrendcheck'] = 1
        else:
            d['desctrendcheck'] = 0

        if closetomean == within1sigma or ((i > 0) and (data[i - 1]['closetomean'] == 1 and data[i - 1]['currSigma'] > abs(data[i - 1]['currAvg'] - d['value']))):
            d['closetomean'] = 1
        else:
            d['closetomean'] = 0
        

        if d['check'] == 1 or d['value'] > d['currUCL']:
            d['highlight'] = 1
        elif d['check'] == -1 or d['value'] < d['currLCL']:
            d['highlight'] = -1
        elif d['asctrendcheck'] == 1:
            d['highlight'] = 1
        elif d['desctrendcheck'] == 1:
            d['highlight'] = -1
        elif d['nearUCLCheck'] == 1:
            d['highlight'] = 1
        elif d['nearLCLCheck'] == 1:
            d['highlight'] = -1
        else:
            d['highlight'] = 0       
        
        prevValue = d['value']

    return(data)

def meanSumCheck(arr, start, num):
    output = 0
    if start + num <= len(arr):
        for i in range(num):
            output = output + (1 if arr[start + i]['value'] > arr[start + i]['currAvg'] else -1)
    return output

def revMeanSumCheck(arr, start, num):
    output = 0
    if start - num >= 0:
        for i in range(num):
            output = output + (1 if arr[start - i]['value'] > arr[start - i]['currAvg'] else -1)
    return output

def trendSumCheck(arr, start, num):
    output = 0
    if start + num < len(arr):
        for i in range(num):
            curr = arr[start + i]['value']
            next = arr[start + i + 1]['value']
            signal = 0
            if curr < next:
                signal = 1
            elif curr > next:
                signal = -1
            output = output + signal
    return output

def revTrendSumCheck(arr, start, num):
    output = 0
    if start + num < len(arr):
        for i in range(num):
            output = output + (1 if arr[start - i]['value']<= arr[start - i - 1]['value'] else -1)
    return output

def closeToMean(arr, start, num):
    output = 0
    if start + num < len(arr):
        for i in range(num):
            output = output + (1 if abs(arr[start + i]['value'] - arr[start + i]['currAvg']) <= arr[start + i]['currSigma'] else -1)
    return output

def nearUCLCheck(arr, start, num):
    output = 0
    abovemean = 0
    if start + num <= len(arr):
        for i in range(num):
            output = output + (1 if arr[start + i]['value'] >= 2*arr[start + i]['currSigma'] + arr[start + i]['currAvg'] and arr[start + i]['value'] <= 3*arr[start + i]['currSigma'] + arr[start + i]['currAvg'] else 0)
            abovemean = abovemean + (1 if arr[start + i]['value'] >= arr[start + i]['currAvg'] else 0)
        if output >= 2 and abovemean == 3:
            for i in range(num):
                if arr[start + i]['value'] >= 2*arr[start + i]['currSigma'] + arr[start + i]['currAvg'] and arr[start + i]['value'] <= 3*arr[start + i]['currSigma'] + arr[start + i]['currAvg']:
                    arr[start + i]['nearUCLCheck'] = 1
                else:
                    arr[start + i]['nearUCLCheck'] = 0
    return arr

def dateFromQlikNumber(n):
    d = datetime.datetime.fromtimestamp((n - 25569) * 86400)
    # since date was created in UTC shift it to the local timezone
    d = d + datetime.timedelta(minutes=d.utcoffset().total_seconds() / 60)
    return d

# Define a function to check how many values are near the lower control limit (LCL) in a given array
def nearLCLCheck(arr, start, num):
    # Initialize the output and belowmean variables to 0
    output = 0
    belowmean = 0
    # Check if the start and num parameters are valid for the array length
    if start + num <= len(arr):
    # Loop through the array from start to start + num
        for i in range(num):
        # Increment output by 1 if the value is between -2 and -3 standard deviations from the mean
            output += 1 if arr[start + i]["value"] <= -2 * arr[start + i]["currSigma"] + arr[start + i]["currAvg"] and arr[start + i]["value"] >= -3 * arr[start + i]["currSigma"] + arr[start + i]["currAvg"] else 0
        # Increment belowmean by 1 if the value is below the mean
            belowmean += 1 if arr[start + i]["value"] <= arr[start + i]["currAvg"] else 0
            # If output is at least 2 and belowmean is 3, mark the values that are near the LCL with a flag
            if output >= 2 and belowmean == 3:
            # Loop through the array again from start to start + num
                for i in range(num):
                    # If the value is between -2 and -3 standard deviations from the mean, set the nearLCLCheck flag to 1
                    if arr[start + i]["value"] <= -2 * arr[start + i]["currSigma"] + arr[start + i]["currAvg"] and arr[start + i]["value"] >= -3 * arr[start + i]["currSigma"] + arr[start + i]["currAvg"]:
                        arr[start + i]["nearLCLCheck"] = 1
                    else:
                        arr[start + i]["nearLCLCheck"] = 0
  # Return the output value
    return arr

  