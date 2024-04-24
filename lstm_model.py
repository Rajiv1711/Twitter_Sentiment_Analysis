# -*- coding: utf-8 -*-
"""LSTM_MODEL.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1NFw4ylg6oXKFXOkb7_kiK6wM3xpSAuji
"""

import pandas as pd
import numpy as np
import nltk
from nltk.stem import WordNetLemmatizer
import matplotlib.pyplot as plt
from copy import deepcopy

"""Reading the Data"""

tweet = pd.read_csv(r"/content/train_data (1).csv")
# tweet = tweet[:1000]

train_df = tweetvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
train_df.head()

"""Downloading the text file for word vector"""

!wget http://downloads.cs.stanford.edu/nlp/data/glove.6B.zip

!unzip glove.6B.zip

"""Funtion to copy the word vector from text file to a dictionary"""

words = dict()

def add_to_dict(d, filename):
  with open(filename, 'r') as f:
    for line in f.readlines():
      line = line.split(' ')

      try:
        d[line[0]] = np.array(line[1:], dtype=float)
      except:
        continue

add_to_dict(words, 'glove.6B.50d.txt')
len(words)

nltk.download('wordnet')

"""Funtion to convert tweets into word tokens"""

tokenizer = nltk.RegexpTokenizer(r"\w+")
lemmatizer = WordNetLemmatizer()

def message_to_token_list(s):
  tokens = tokenizer.tokenize(s)
  lowercased_tokens = [t.lower() for t in tokens]
  lemmatized_tokens = [lemmatizer.lemmatize(t) for t in lowercased_tokens]
  useful_tokens = [t for t in lemmatized_tokens if t in words]

  return useful_tokens

"""Function to convert wrod tokens into word vectors using vector dictionary"""

def message_to_word_vectors(message, word_dict=words):
  processed_list_of_tokens = message_to_token_list(message)

  vectors = []

  for token in processed_list_of_tokens:
    if token not in word_dict:
      continue

    token_vector = word_dict[token]
    vectors.append(token_vector)

  return np.array(vectors, dtype=float)

"""Splitting the training data into 3 parts

1.   Training data frame
2.   Validation data frame
3.   Test data frame
"""

train_df = train_df.sample(frac=1, random_state=1)
train_df.reset_index(drop=True, inplace=True)

split_index_1 = int(len(train_df) * 0.6)
split_index_2 = int(len(train_df) * 0.7)

train_df, val_df, test_df = train_df[:split_index_1], train_df[split_index_1:split_index_2], train_df[split_index_2:]

len(train_df), len(val_df), len(test_df)

test_df

"""Function to define the input/output data"""

def df_to_X_y(dff):
  y = dff['label'].to_numpy().astype(int)

  all_word_vector_sequences = []

  for message in dff['tweet']:
    message_as_vector_seq = message_to_word_vectors(message)

    if message_as_vector_seq.shape[0] == 0:
      message_as_vector_seq = np.zeros(shape=(1, 50))

    all_word_vector_sequences.append(message_as_vector_seq)

  return all_word_vector_sequences, y

X_train, y_train = df_to_X_y(train_df)

print(len(X_train), len(X_train[10]))

"""analysing the length of most tweet's useful tokens/vector"""

sequence_lengths = []

for i in range(len(X_train)):
  sequence_lengths.append(len(X_train[i]))

pd.Series(sequence_lengths).describe()

"""Padding the word token/vector list to convert them into numpy array"""

def pad_X(X, desired_sequence_length=59):
  X_copy = deepcopy(X)

  for i, x in enumerate(X):
    x_seq_len = x.shape[0]
    sequence_length_difference = desired_sequence_length - x_seq_len

    pad = np.zeros(shape=(sequence_length_difference, 50))

    X_copy[i] = np.concatenate([x, pad])

  return np.array(X_copy).astype(float)

"""padding the training data Frames"""

X_train = pad_X(X_train)

X_train.shape

"""padding the validation data Frames"""

X_val, y_val = df_to_X_y(val_df)
X_val = pad_X(X_val)

X_val.shape, y_val.shape

"""padding the test data Frames"""

X_test, y_test = df_to_X_y(test_df)
X_test = pad_X(X_test)

X_test.shape, y_test.shape

"""# **LSTM Model**

Defining the LSTM model
"""

from tensorflow.keras import layers
from tensorflow.keras.models import Sequential
from keras.layers import Embedding, LSTM, Dense, Dropout,Bidirectional,SimpleRNN

lstm_model = Sequential([])

lstm_model.add(layers.Input(shape=(59, 50)))
lstm_model.add(LSTM(64, return_sequences=True))
lstm_model.add(Dropout(0.2))
lstm_model.add(LSTM(64, return_sequences=True))
lstm_model.add(Dropout(0.2))
lstm_model.add(LSTM(64, return_sequences=True))
lstm_model.add(Dropout(0.2))
lstm_model.add(layers.Flatten())
lstm_model.add(Dense(1, activation='sigmoid'))

"""Compiling the LSTM model"""

from tensorflow.keras.losses import BinaryCrossentropy
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.metrics import AUC
from tensorflow.keras.callbacks import ModelCheckpoint

cp = ModelCheckpoint('model/', save_best_only=True)

lstm_model.compile(optimizer=Adam(learning_rate=0.001),
              loss=BinaryCrossentropy(),
              metrics=['accuracy', AUC(name='auc')])

"""calculation for optimizing the model (as the dataset is not balanced)"""

frequencies = pd.value_counts(train_df['label'])

frequencies

weights = {0: frequencies.sum() / frequencies[0], 1: frequencies.sum() / frequencies[1]}
weights

"""Training the LSTM model"""

lstm_model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=10, callbacks=[cp], class_weight = weights)

"""Saving the best model"""

from tensorflow.keras.models import load_model

best_model = load_model('model/')

"""Printing the trained model prediction report"""

test_predictions = (best_model.predict(X_test) > 0.5).astype(int)

from sklearn.metrics import classification_report

print(classification_report(y_test, test_predictions))