import pandas as pd
from sklearn import preprocessing
from sklearn import decomposition
from train import glucoseFeatures
import pickle


with open("model.pkl", 'rb') as file:
        loaded_model = pickle.load(file) 
        test_df = pd.read_csv('test.csv', header=None)
    
features = glucoseFeatures(test_df)
stand_scaler_fit = preprocessing.StandardScaler().fit_transform(features)
    
pca = decomposition.PCA(n_components=5)
pca_fit = pca.fit_transform(stand_scaler_fit)
    
results = loaded_model.predict(pca_fit)
pd.DataFrame(results).to_csv("Results.csv", header=None, index=False)


zeroCount = 0
oneCount = 0

for i in results:
        if i == 0:
                zeroCount += 1
        elif i == 1:
                oneCount += 1


print('zeroCount', zeroCount)

print('oneCount', oneCount)
