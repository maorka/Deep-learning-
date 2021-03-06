# -*- coding: utf-8 -*-
"""Copy of Copy of Dicom predictions

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1si1SYJKvImIXXg3i521MR6yTCTlL7jF1

## 1. Import Packages
"""

# dicom installation 
!pip install dicom
!pip install pydicom

# Commented out IPython magic to ensure Python compatibility.
import numpy as np
import pandas as pd
import dicom
import random
from keras.models import Sequential, Model
import keras.layers as layers
from keras.utils import to_categorical
from keras import optimizers
from keras.optimizers import SGD
from keras.models import model_from_json
from keras.layers import Input
import matplotlib.pyplot as plt
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.datasets import load_iris
from tqdm import tqdm
from google.colab import files

from sklearn.metrics import confusion_matrix
from skimage.transform import resize
import re
from keras.applications.vgg16 import VGG16, preprocess_input
from keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow import keras
from keras.models import Sequential
from keras.layers import Dense, Flatten, Conv2D, Input, MaxPooling2D, BatchNormalization,Dropout
from keras.layers import Flatten

# to paint loaded dicom images for debug:
from PIL import Image
import numpy as np
from matplotlib.pyplot import imshow
# %matplotlib inline

"""## 2. Load Data"""

#load images(Dicom files from drive)
import glob
from google.colab import drive
drive.mount('/content/drive')
root_path = 'drive/My Drive/INBreast Dataset/'
images = glob.glob(root_path + '/ALL-IMGS/'+ '/*.dcm')

#verify the images was loaded
print(images)
len(images)

#load Excel Data-set file
excel_data = pd.read_excel("drive/My Drive/INBreast Dataset/INbreast.xls",0,encoding='cp1252',
                           converters={'File Name':str})

#validating Excel-was loaded
print(excel_data.head())
print(excel_data.tail())
print(excel_data.columns)

#New Data-set-convert dicmImages to list of matrixes
data_set_x_train = []
for img_file in tqdm(images):
  ds = dicom.read_file(img_file)
  data_set_x_train.append(ds.pixel_array)

# shuffle the training data (in the same manner everytime)
random.Random(1331).shuffle(data_set_x_train)

# Verify Images become a list of numpy arrays
print(len(data_set_x_train))
print(data_set_x_train[0].shape)

#Binary Labales,x>=4-->sick=0,x<4-->Healty=1
# extract targets
#list of labales/integers
#Pandas tolist() methods is used to convert a series to list.
labels = excel_data['Bi-Rads'].tolist()
#list of images_numbers/strings
files = excel_data['File Name'].tolist()
# 4a/4b/4c -> 4 + convert list of integers to list of strings
y_train_temp_1 = list(re.findall(r'[0-9]+',str(labels)))
#convert list of strings to list of integers
y_train_temp = [0 if int(info) >= 4 else 1 for info in y_train_temp_1]
#match between labels and images,manually -create of dictionary
#zip function Join two tuples/list together-labels and images_names-join to dictionary
file_to_target = {fname: target for fname, target in zip(files, y_train_temp)}
#validation of binary labels
print(file_to_target)
len(file_to_target)

# format it to match data_set_x_train
#match between the dictionary(labales&images) and to the images
data_set_y_train = []
for filename in images:
  for fkey in file_to_target.keys():
    if fkey in filename:
      data_set_y_train.append(file_to_target[fkey])
      break

# print/inspect one from loaded images (and targetclasses)-final matching verifing
imgfile, image, target = images[0], data_set_x_train[0], data_set_y_train[0]
print(imgfile)#print image in dicom list
print(image.shape)#verify size of image
print(target)#verify label of image
imshow(image)#plot image for example

#reshape to all images-to be all be with the same size

# look at image sizes-before reshapining
shapes_temp = [img.shape for img in data_set_x_train]
print(set(shapes_temp))
#set function shuffle the list/dictionary and print a couple of the objects randomly 
# since the shapes are different, lets convert it to one shape
data_set_x_train = [resize(img, (664, 512)) if img.shape[0] > 664 else img for img in tqdm(data_set_x_train)]
print(data_set_x_train[0].shape)
imshow(data_set_x_train[0])

#verify all shapes now match-after reshapinig
shapes = [img.shape for img in data_set_x_train]
print(set(shapes))

# turn all lists into np matrices
all_train_x_arr = np.expand_dims(np.stack(data_set_x_train, axis=0), -1)
all_train_y_arr = np.expand_dims(np.stack(data_set_y_train, axis=0), -1)
print(all_train_x_arr.shape)
print(all_train_y_arr.shape)

# split the data to train and test set
# split the data to train and validation and testing->80,10,10


total = len(all_train_y_arr)
split = int(total*0.8)
split2=int(total*0.9)

x_train = all_train_x_arr[:split]
y_train = all_train_y_arr[:split]


x_val = all_train_x_arr[split:split2]
y_val = all_train_y_arr[split:split2]
x_test = all_train_x_arr[split2:]
y_test = all_train_y_arr[split2:]

# Change labels to one-hot encoding
x_train= to_categorical(x_train)
y_train = to_categorical(y_train)
y_test =to_categorical(y_test)

x_val = to_categorical(x_val)
y_val =to_categorical(y_val)

print('x_train shape:',np.shape(x_train))
print('x_test shape:', np.shape(x_test))
print('y_train shape:',np.shape(y_train))
print('y_test shape:', np.shape(y_test))

"""## 3. Define Parameters"""

epochs = 20            # number of epochs 
bs =  16                 # batch size
num_of_clss = 2           # number of classes
lr =0.01                # learning rate 
dp = 0.6                 # dropout probability

"""## 4. Build Network"""

#Use another training from another data set,and stop whenever you want

# base_model = VGG16(weights = "imagenet", include_top=False, 
#                    input_shape=(x_train.shape[1],x_train.shape[2],x_train.shape[3]))

# # Extract the last layer from third block of vgg16 model
# last = base_model.get_layer('block3_pool').output

# # Freeze the layers of the vgg which we don't want to train.
# # Fine-Tune the third conv block
# for layer in base_model.layers[:7]:
#     layer.trainable = False


# define a convolutional network
inp = Input(shape = [x_train.shape[1],x_train.shape[2], x_train.shape[3]])
pic_conv_kernel_size = 5

# x = Flatten()(last)
# x = Dense(256, activation='relu')(x)

# # First conv block
pic_1 = Conv2D(64, pic_conv_kernel_size, padding='same', strides=1, activation='relu')(inp)
#x = BatchNormalization()(pic_1)-doesn't-work on first block
pic_2 = MaxPooling2D(pool_size=2)(pic_1)

# # Second conv block
# x = Dense(256, activation='relu')(x)
# x = Flatten()(last)
pic_3 = Conv2D(32, pic_conv_kernel_size, padding='same', strides=1, activation='relu')(pic_2)
x1 = BatchNormalization()(pic_3)
x = Dropout(dp)(x1)
pic_4 = MaxPooling2D(pool_size=2)(x) 

# # Third conv block
pic_5 = Conv2D(32, pic_conv_kernel_size, padding='same', dilation_rate=3, activation='relu')(pic_4)
x2 = BatchNormalization()(pic_5 )
x = Dropout(dp)(x2)
#z = Dense(y_train.shape[-1], activation='relu')(x)
pic_6 = MaxPooling2D(pool_size=2)(x)

# # 4th conv block
pic_7 = Conv2D(32, pic_conv_kernel_size, padding='same', dilation_rate=3, activation='relu')(pic_6)
x3 = BatchNormalization()(pic_7)
x4 = Dropout(dp)(x3)
#y = Dense(y_train.shape[-1], activation='relu')(x4)
pic_8 = MaxPooling2D(pool_size=2)(x4)

#Fully connected 
pic_9 = Flatten()(pic_8)
pic_final = Dense(num_of_clss, activation='sigmoid')(pic_9)#pic_final=prediction layer



model = Model(inp, pic_final)
model.summary()

"""##  5. Train the Model"""

# define the optimizer, early stopping and model saving and compile the model
#adam = optimizers.Adam(lr=lr, beta_1=beta_1, beta_2=beta_2, epsilon=epsilon)

#1)compile the model
opt = SGD(lr)
model.compile(loss = "binary_crossentropy", optimizer = opt,metrics=['accuracy'])

#model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# add early stopping
monitor = EarlyStopping(monitor='val_loss', min_delta=1e-4, patience=5, verbose=1, mode='auto')
#A checkpointer is a mechanic to save the trained parameters

checkpointer = ModelCheckpoint('best.h5',
                                 monitor='val_loss', save_best_only=True, verbose=1)
# Train the model
history = model.fit(x_train, y_train, validation_data=(x_val,y_val), epochs=epochs, batch_size=bs, callbacks=[monitor, checkpointer])

#load the saved best weights for further analysis
model.load_weights("best.h5")

"""## 6. Visualize"""

# plot train and validation loss 
plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('model loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'validation'], loc='upper left')
plt.show()
plt.close()

######################################################prediction#########################################################
y_pred = model.predict(x_test)
test_loss, test_acc = model.evaluate(x_test, y_test)#test loss-less critical-need to look about test accurac->1
# Print results
print('test loss:', test_loss)
print('test accuracy:', test_acc)



# #plot confusion matrix

cm=confusion_matrix(y_test.argmax(axis=1),np.round(y_pred.argmax(axis=1)))

plt.clf()
plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Wistia)
classNames = ['Negative','Positive']
plt.title('Versicolor or Not Versicolor Confusion Matrix - Test Data')
plt.ylabel('True label')
plt.xlabel('Predicted label')
tick_marks = np.arange(len(classNames))
plt.xticks(tick_marks, classNames, rotation=45)
plt.yticks(tick_marks, classNames)
s = [['TN','FP'], ['FN', 'TP']]
for i in range(num_of_clss):
    for j in range(num_of_clss):
        plt.text(j,i, str(s[i][j])+" = "+str(cm[i][j]))
plt.show()

# cm=confusion_matrix(
#     y_test.argmax(axis=1), y_pred.argmax(axis=1))
# print(cm)

#confusion matrix in percentage 

# from google.colab import files
# src = list(files.upload().values())[0]
# open('plot_confusion_matrix.py','wb').write(src)
# from sklearn.metrics import confusion_matrix
# from plot_confusion_matrix import plot_confusion_matrix
# # Confusion Matrix
# cm = confusion_matrix(np.argmax(y_test,axis=1), np.argmax(np.round(y_pred),axis=1))
# labels = ['class ' + str(i) for i in range(num_of_clss)] 
# plot_confusion_matrix(cm,labels,title='Confusion Matrix',normalize=True)
