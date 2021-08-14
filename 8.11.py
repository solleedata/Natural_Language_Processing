# -*- coding: utf-8 -*-
"""8-12.KoGPT2(gen_text).ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ABZelGJI7VxTiwsnmD6Fy3o85hxXfmw0
"""

# GPT2의 TFGPT2LMHeadModel 모델을 이용한 언어 생성
# TFGPT2LMHeadModel : The GPT2 Model transformer with a language modeling head on top 
#                     (linear layer with weights tied to the input embeddings).
# !pip install --upgrade mxnet>=1.6.0
# !pip install gluonnlp
# !pip install transformers
# !pip install sentencepiece

import gluonnlp as nlp
from gluonnlp.data import SentencepieceTokenizer, SentencepieceDetokenizer
from transformers import TFGPT2LMHeadModel
import tensorflow as tf

MY_PATH = '/content/drive/MyDrive/Colab Notebooks/'
MODEL_PATH = MY_PATH + 'gpt_ckpt'
TOKENIZER_PATH = MY_PATH + 'gpt_ckpt/gpt2_kor_tokenizer.spiece'

tokenizer = SentencepieceTokenizer(TOKENIZER_PATH)
detokenizer = SentencepieceDetokenizer(TOKENIZER_PATH)
vocab = nlp.vocab.BERTVocab.from_sentencepiece(TOKENIZER_PATH,
                                               mask_token = None,
                                               sep_token = None,
                                               cls_token = None,
                                               unknown_token = '<unk>',
                                               padding_token = '<pad>',
                                               bos_token = '<s>',
                                               eos_token = '</s>')
# vocab --> Vocab(size=50000, unk="<unk>", reserved="['<pad>', '<s>', '</s>']")

# tokenizer 연습
# 참고 : https://nlp.gluon.ai/api/modules/data.html
toked = tokenizer('안녕 하세요')   # tokenizer가 잘못 만들어진 듯 ... 한글자씩 ?
print(toked)

toked_idx = vocab(toked)
print(toked_idx)

toked = vocab.to_tokens(toked_idx)
print(toked)

detoked = detokenizer(toked)
print(detoked)

''.join(toked).replace('▁', ' ')

model = TFGPT2LMHeadModel.from_pretrained(MODEL_PATH)
model.summary()

# 모델의 seed 입력 문장 생성
tok = tokenizer('이때')   # tok = ['▁', '이', '때']
tok_idx = [vocab[vocab.bos_token]] + vocab[tok]     # tok_idx = [0, 47437, 47438, 47675]
input_ids = tf.convert_to_tensor(tok_idx)[None, :]  # 텐서로 변환

# 모델의 출력
output = model.generate(input_ids, max_length=50)

output

# 모델의 출력을 문자열로 변환
out_tok_idx = output.numpy().tolist()[0]   # output token 인덱스
out_tok = vocab.to_tokens(out_tok_idx)     # token 인덱스를 token 문자로 변환
out_text = detokenizer(out_tok)            # 출력 문자열로 decode
print(out_text)

# Beam search
output = model.generate(input_ids, max_length=50, num_beams=5, early_stopping=True)

out_tok_idx = output.numpy().tolist()[0]   # output token 인덱스
out_tok = vocab.to_tokens(out_tok_idx)     # token 인덱스를 token 문자로 변환
out_text = detokenizer(out_tok)            # 출력 문자열로 decode
print(out_text)

# 연속된 단어가 나오는 것을 방지함. no_repeat_ngram_size = 2
output = model.generate(input_ids, max_length=50, num_beams=5, no_repeat_ngram_size=2, early_stopping=True)

out_tok_idx = output.numpy().tolist()[0]   # output token 인덱스
out_tok = vocab.to_tokens(out_tok_idx)     # token 인덱스를 token 문자로 변환
out_text = detokenizer(out_tok)            # 출력 문자열로 decode
print(out_text)

# top_k sampling
output = model.generate(input_ids, max_length=50, do_sample = True, top_k=100, temperature=0.8)

out_tok_idx = output.numpy().tolist()[0]   # output token 인덱스
out_tok = vocab.to_tokens(out_tok_idx)     # token 인덱스를 token 문자로 변환
out_text = detokenizer(out_tok)            # 출력 문자열로 decode
print(out_text)

# top_p sampling
output = model.generate(input_ids, max_length=50, do_sample = True, top_p=0.9, temperature=0.8)

out_tok_idx = output.numpy().tolist()[0]   # output token 인덱스
out_tok = vocab.to_tokens(out_tok_idx)     # token 인덱스를 token 문자로 변환
out_text = detokenizer(out_tok)            # 출력 문자열로 decode
print(out_text)

# top_k & top_p sampling
output = model.generate(input_ids, max_length=50, do_sample = True, top_k=100, top_p=0.9, temperature=0.8)

out_tok_idx = output.numpy().tolist()[0]   # output token 인덱스
out_tok = vocab.to_tokens(out_tok_idx)     # token 인덱스를 token 문자로 변환
out_text = detokenizer(out_tok)            # 출력 문자열로 decode
print(out_text)


#TODO:
# -*- coding: utf-8 -*-
"""8-13.naver_movie(kogpt2).ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1N396gN4Jh6cidXhylM0s-Pp1epRGREl-
"""

# KoGPT2를 이용한 네이버 영화 감성분석
# !pip install --upgrade mxnet>=1.6.0
# !pip install gluonnlp
# !pip install transformers
# !pip install sentencepiece

import gluonnlp as nlp
from gluonnlp.data import SentencepieceTokenizer, SentencepieceDetokenizer
from transformers import TFGPT2LMHeadModel
import tensorflow as tf

import pandas as pd
import numpy as np
from tensorflow.keras.layers import Dense, Input
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from sklearn.model_selection import train_test_split
from tensorflow.keras.preprocessing.sequence import pad_sequences
import re
from tqdm import tqdm
import matplotlib.pyplot as plt

# Commented out IPython magic to ensure Python compatibility.
# %cd '/content/drive/MyDrive/Colab Notebooks'
df = pd.read_csv('data/naver_movie/ratings.txt', header=0, delimiter='\t', quoting=3)
df = df.dropna()
df.head()

# "\d+"는 숫자 1개 이상을 의미함. 모든 숫자를 공백으로 치환
df['document'] = df['document'].apply(lambda x: re.sub(r"\d+", " ", x))
df.drop('id', axis = 1, inplace = True)

document = list(df['document'])
label = list(df['label'])
dx_train, dx_test, dy_train, dy_test = train_test_split(document, label, test_size=0.2)

MY_PATH = '/content/drive/MyDrive/Colab Notebooks/'
MODEL_PATH = MY_PATH + 'gpt_ckpt'
TOKENIZER_PATH = MY_PATH + 'gpt_ckpt/gpt2_kor_tokenizer.spiece'

tokenizer = SentencepieceTokenizer(TOKENIZER_PATH, num_best=0, alpha=0)
detokenizer = SentencepieceDetokenizer(TOKENIZER_PATH)
vocab = nlp.vocab.BERTVocab.from_sentencepiece(TOKENIZER_PATH,
                                               mask_token = None,
                                               sep_token = None,
                                               cls_token = None,
                                               unknown_token = '<unk>',
                                               padding_token = '<pad>',
                                               bos_token = '<s>',
                                               eos_token = '</s>')
# vocab --> Vocab(size=50000, unk="<unk>", reserved="['<pad>', '<s>', '</s>']")

MAX_LEN = 60

def build_data(x_data, y_label):
    data_sents = []
    data_labels = []

    for sent, label in zip(x_data, y_label):
        tokenized_text = vocab[tokenizer(sent)]

        tokens = [vocab[vocab.bos_token]]  
        tokens += pad_sequences([tokenized_text], 
                                MAX_LEN, 
                                value=vocab[vocab.padding_token], 
                                padding='post').tolist()[0] 
        tokens += [vocab[vocab.eos_token]]

        data_sents.append(tokens)
        data_labels.append(label)

    return np.array(data_sents, dtype=np.int64), np.array(data_labels, dtype=np.int64).reshape(-1, 1)

# 시험용으로 100개씩만 사용한다.
x_train, y_train = build_data(dx_train[:100], dy_train[:100])
x_test, y_test = build_data(dx_test[:100], dy_test[:100])

x_train.shape, y_train.shape, x_test.shape, y_test.shape

x_test[0]

len(x_test[0])

print(len(vocab))
print(vocab.padding_token, ':', vocab[vocab.padding_token])
print(vocab.bos_token, ': ', vocab[vocab.bos_token])
print(vocab.eos_token, ': ', vocab[vocab.eos_token])
print(vocab.unknown_token, ': ', vocab[vocab.unknown_token])

word2idx = {k:v for k, v in vocab.token_to_idx.items()}
idx2word = {v:k for k, v in word2idx.items()}
idx2word[5000]

# 참고 : https://nlp.gluon.ai/api/modules/data.html
tokenizer('나는 자연어처리를 공부하고 있다')

print([idx2word[i] for i in x_test[0]])

gpt_model = TFGPT2LMHeadModel.from_pretrained(MODEL_PATH)
gpt_model.summary()

# TFGPT2MainLayer는 fine-tuning을 하지 않는다.
gpt_model.trainable = False
gpt_model.summary() # gtp_model을 다시 확인한다. trainable params = 0

# GPT2 입력
# ---------
x_input = Input(batch_shape = (None, MAX_LEN + 2), dtype = tf.int32)

# GPT2 출력
# ---------
# output_gpt[0]        --> <KerasTensor: shape=(None, 60, 50000) dtype=float32
# output_gpt[0][:, -1] --> <KerasTensor: shape=(None, 50000) dtype=float32
output_gpt = gpt_model(x_input)[0][:, -1]

# Downstream task : 네이버 영화 감성분석
# -------------------------------------
y_output = Dense(1, activation = 'sigmoid')(output_gpt)
model = Model(x_input, y_output)
model.compile(loss = 'binary_crossentropy', optimizer = Adam(learning_rate = 0.001))
model.summary()

hist = model.fit(x_train, y_train, validation_data = (x_test, y_test), epochs=3, batch_size=1024)

# 1/1 [==============================] - 14s 14s/step - loss: 0.7251 - val_loss: 70.8553
# Epoch 2/3
# 1/1 [==============================] - 1s 1s/step - loss: 69.2513 - val_loss: 26.5999
# Epoch 3/3
# 1/1 [==============================] - 1s 1s/step - loss: 25.5047 - val_loss: 21.4767

# Loss history를 그린다
plt.plot(hist.history['loss'], label='Train loss')
plt.plot(hist.history['val_loss'], label = 'Test loss')
plt.legend()
plt.title("Loss history")
plt.xlabel("epoch")
plt.ylabel("loss")
plt.show()

# 시험 데이터로 학습 성능을 평가한다
pred = model.predict(x_test)
y_pred = np.where(pred > 0.5, 1, 0)
accuracy = (y_pred == y_test).mean()
print("\nAccuracy = %.2f %s" % (accuracy * 100, '%'))

# gpt_model.trainable = True로 바꾸고, learning-rate를 작게 적용해서
# 전체를 다시 학습한다. (미세 조정)


#TODO:
# -*- coding: utf-8 -*-
"""8-14.naver_movie(kogpt2_2).ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1oz7cwQ6Wv116SfshytDb3w68i_oaK7W6
"""

# KoGPT2를 이용한 네이버 영화 감성분석
# 참고 : https://github.com/SKT-AI/KoGPT2
!pip install --upgrade mxnet>=1.6.0
!pip install gluonnlp
!pip install transformers
!pip install sentencepiece

import gluonnlp as nlp
from gluonnlp.data import SentencepieceTokenizer, SentencepieceDetokenizer
from transformers import TFGPT2LMHeadModel
import tensorflow as tf

import pandas as pd
import numpy as np
from tensorflow.keras.layers import Dense, Input, Concatenate, GlobalAveragePooling1D
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from sklearn.model_selection import train_test_split
from tensorflow.keras.preprocessing.sequence import pad_sequences
import re
from tqdm import tqdm
import matplotlib.pyplot as plt

# Commented out IPython magic to ensure Python compatibility.
# %cd '/content/drive/MyDrive/Colab Notebooks'
df = pd.read_csv('data/naver_movie/ratings.txt', header=0, delimiter='\t', quoting=3)
df = df.dropna()
df.head()

# "\d+"는 숫자 1개 이상을 의미함. 모든 숫자를 공백으로 치환
df['document'] = df['document'].apply(lambda x: re.sub(r"\d+", " ", x))
df.drop('id', axis = 1, inplace = True)

document = list(df['document'])
label = list(df['label'])
dx_train, dx_test, dy_train, dy_test = train_test_split(document, label, test_size=0.2)

MY_PATH = '/content/drive/MyDrive/Colab Notebooks/'
MODEL_PATH = MY_PATH + 'gpt_ckpt'
TOKENIZER_PATH = MY_PATH + 'gpt_ckpt/gpt2_kor_tokenizer.spiece'

tokenizer = SentencepieceTokenizer(TOKENIZER_PATH, num_best=0, alpha=0)
detokenizer = SentencepieceDetokenizer(TOKENIZER_PATH)
vocab = nlp.vocab.BERTVocab.from_sentencepiece(TOKENIZER_PATH,
                                               mask_token = None,
                                               sep_token = None,
                                               cls_token = None,
                                               unknown_token = '<unk>',
                                               padding_token = '<pad>',
                                               bos_token = '<s>',
                                               eos_token = '</s>')
# vocab --> Vocab(size=50000, unk="<unk>", reserved="['<pad>', '<s>', '</s>']")

MAX_LEN = 60

def build_data(x_data, y_label):
    data_sents = []
    data_labels = []

    for sent, label in zip(x_data, y_label):
        tokenized_text = vocab[tokenizer(sent)]

        tokens = [vocab[vocab.bos_token]]   # 시작 = <s>
        tokens += pad_sequences([tokenized_text], 
                                MAX_LEN, 
                                value=vocab[vocab.padding_token], 
                                padding='post').tolist()[0] 
        tokens += [vocab[vocab.eos_token]]  # 끝 = </s>

        data_sents.append(tokens)
        data_labels.append(label)

    return np.array(data_sents, dtype=np.int64), np.array(data_labels, dtype=np.int64).reshape(-1, 1)

# 시험용으로 100개씩만 사용한다.
x_train, y_train = build_data(dx_train[:100], dy_train[:100])
x_test, y_test = build_data(dx_test[:100], dy_test[:100])

x_train.shape, y_train.shape, x_test.shape, y_test.shape

x_test[0]

len(x_test[0])

print(len(vocab))
print(vocab.padding_token, ':', vocab[vocab.padding_token])
print(vocab.bos_token, ': ', vocab[vocab.bos_token])
print(vocab.eos_token, ': ', vocab[vocab.eos_token])
print(vocab.unknown_token, ': ', vocab[vocab.unknown_token])

word2idx = {k:v for k, v in vocab.token_to_idx.items()}
idx2word = {v:k for k, v in word2idx.items()}
idx2word[5000]

# 참고 : https://nlp.gluon.ai/api/modules/data.html
sub_word = tokenizer('나는 자연어처리를 공부하고 있다')
print(sub_word)

sent_idx = vocab[sub_word]
print(sent_idx)

print(detokenizer(sub_word))

print([idx2word[i] for i in x_test[0]])

gpt_model = TFGPT2LMHeadModel.from_pretrained(MODEL_PATH)
gpt_model.summary()

# TFGPT2MainLayer는 fine-tuning을 하지 않는다.
gpt_model.trainable = False
gpt_model.summary() # gtp_model을 다시 확인한다. trainable params = 0

# GPT2 입력
# ---------
x_input = Input(batch_shape = (None, MAX_LEN + 2), dtype = tf.int32)  # <s>와 </s> 2개 포함

# GPT2 출력
# ---------
# for classification
# output_gpt[0]           --> <KerasTensor: shape=(None, 62, 50000) dtype=float32
# output_gpt[0][:, -1, :] --> <KerasTensor: shape=(None, 50000) dtype=float32
#
# output_gpt 전체 출력 :
# TFCausalLMOutputWithPast([('logits',
#                            <KerasTensor: shape=(None, 62, 50000) dtype=float32 (created by layer 'tfgp_t2lm_head_model')>),
#                           ('past_key_values',
#                            (<KerasTensor: shape=(2, None, 12, 62, 64) dtype=float32 (created by layer 'tfgp_t2lm_head_model')>,
#                             <KerasTensor: shape=(2, None, 12, 62, 64) dtype=float32 (created by layer 'tfgp_t2lm_head_model')>,
#                             <KerasTensor: shape=(2, None, 12, 62, 64) dtype=float32 (created by layer 'tfgp_t2lm_head_model')>,
#                             <KerasTensor: shape=(2, None, 12, 62, 64) dtype=float32 (created by layer 'tfgp_t2lm_head_model')>,
#                             <KerasTensor: shape=(2, None, 12, 62, 64) dtype=float32 (created by layer 'tfgp_t2lm_head_model')>,
#                             <KerasTensor: shape=(2, None, 12, 62, 64) dtype=float32 (created by layer 'tfgp_t2lm_head_model')>,
#                             <KerasTensor: shape=(2, None, 12, 62, 64) dtype=float32 (created by layer 'tfgp_t2lm_head_model')>,
#                             <KerasTensor: shape=(2, None, 12, 62, 64) dtype=float32 (created by layer 'tfgp_t2lm_head_model')>,
#                             <KerasTensor: shape=(2, None, 12, 62, 64) dtype=float32 (created by layer 'tfgp_t2lm_head_model')>,
#                             <KerasTensor: shape=(2, None, 12, 62, 64) dtype=float32 (created by layer 'tfgp_t2lm_head_model')>,
#                             <KerasTensor: shape=(2, None, 12, 62, 64) dtype=float32 (created by layer 'tfgp_t2lm_head_model')>,
#                             <KerasTensor: shape=(2, None, 12, 62, 64) dtype=float32 (created by layer 'tfgp_t2lm_head_model')>))])
# past_key_values : 중간 출력
# (2, None, 12, 62, 64)
# 2 : Text prediction과 Task classifier (GPT-1 논문의 figure-1)
# None : batch
# 12 : number of layers
# 62 : MAX_LEN
# 64 : d_model / num_heads = 768 / 12 = 64 = dk <-- multi-head attention의 각 head의 출력
#      64개 head를 concat으로 묶으면 768 embedding vector size.
#
# https://opensourcelibs.com/lib/kogpt2#mxnet-gluon
# GPT2Model(units=768,
#     max_length=1024,
#     num_heads=12,
#     num_layers=12,
#     dropout=0.1,
#     vocab_size=50000)
output_gpt = gpt_model(x_input)

# 'past_key_values' 출력을 이용한다.
# 마지막 layer의 multi head attension 출력
output_mha = output_gpt[1][0][0, :, -1, :, :]
for i in range(1, 12):
    output_mha = Concatenate()([output_mha, output_gpt[1][i][0, :, -1, :, :]])
output_mha = GlobalAveragePooling1D()(output_mha)

# Downstream task : 네이버 영화 감성분석
# -------------------------------------
y_output = Dense(1, activation = 'sigmoid')(output_mha)
model = Model(x_input, y_output)
model.compile(loss = 'binary_crossentropy', optimizer = Adam(learning_rate = 0.001))
model.summary()

hist = model.fit(x_train, y_train, validation_data = (x_test, y_test), epochs=3, batch_size=1024)

# 1/1 [==============================] - 14s 14s/step - loss: 0.7251 - val_loss: 70.8553
# Epoch 2/3
# 1/1 [==============================] - 1s 1s/step - loss: 69.2513 - val_loss: 26.5999
# Epoch 3/3
# 1/1 [==============================] - 1s 1s/step - loss: 25.5047 - val_loss: 21.4767

# Loss history를 그린다
plt.plot(hist.history['loss'], label='Train loss')
plt.plot(hist.history['val_loss'], label = 'Test loss')
plt.legend()
plt.title("Loss history")
plt.xlabel("epoch")
plt.ylabel("loss")
plt.show()

# 시험 데이터로 학습 성능을 평가한다
pred = model.predict(x_test)
y_pred = np.where(pred > 0.5, 1, 0)
accuracy = (y_pred == y_test).mean()
print("\nAccuracy = %.2f %s" % (accuracy * 100, '%'))

# gpt_model.trainable = True로 바꾸고, learning-rate를 작게 적용해서
# 전체를 다시 학습한다. (미세 조정)