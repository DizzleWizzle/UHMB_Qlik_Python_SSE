import nltk
nltk.download('wordnet')

wn = nltk.WordNetLemmatizer()

ps = nltk.PorterStemmer()

#dir(wn)

print(wn.lemmatize('goose'))

print(wn.lemmatize('geese'))

print(ps.stem('testing'))

print(ps.stem('carries'))



car = {
  "brand": "Ford",
  "model": "Mustang",
  "year": 1964
}

print(car)

car['MR']= 'test'

print(car)