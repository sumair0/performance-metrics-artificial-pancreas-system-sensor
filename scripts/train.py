import pandas as pd
import numpy as np
from sklearn import decomposition, preprocessing
from sklearn import model_selection
from sklearn import svm
from sklearn import metrics
from scipy.fftpack import fft
import pickle
# from xgboost import XGBClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
import warnings
warnings.filterwarnings('ignore')


def meal_no_meal_slots(new_slots,slot_difference):
    meal_Times=[]
    firstSlot = new_slots[0 : len(new_slots) - 1]
    secondSlot = new_slots[1 : len(new_slots)]
    difference = list(np.array(firstSlot) - np.array(secondSlot))
    values = list(zip(firstSlot, secondSlot, difference))
    for i in values:
        if i[2]<slot_difference:
            meal_Times.append(i[0])
    return meal_Times

def get_meal_no_meal_data_DF(meal_Times,begin_time,end_time,is_meal_data,new_glucose_DF):
    new_meal = []
    
    for new_Time in meal_Times:
        meal_index = new_glucose_DF[new_glucose_DF['datetime'].between(new_Time + pd.DateOffset(hours=begin_time),new_Time + pd.DateOffset(hours=end_time))]
        if meal_index.shape[0] < 24:
            continue
        glucose_vals = meal_index['Sensor Glucose (mg/dL)'].to_numpy()
        mean = meal_index['Sensor Glucose (mg/dL)'].mean()
        if is_meal_data:
            count_missing_val = 30 - len(glucose_vals)
            if count_missing_val > 0:
                for i in range(count_missing_val):
                    glucose_vals = np.append(glucose_vals, mean)
            new_meal.append(glucose_vals[0:30])
        else:
            new_meal.append(glucose_vals[0:24])
    return pd.DataFrame(data=new_meal)

def meal_no_meal_data(insulin_DF,glucose_DF):
    meal_data_DF = pd.DataFrame()
    no_meal_data_DF = pd.DataFrame()
    standard_scaler = preprocessing.StandardScaler()
    pca = decomposition.PCA(n_components=5)

    insulin_DF= insulin_DF[::-1]
    insulin_DF['datetime'] = pd.to_datetime(insulin_DF["Date"].astype(str) + " " + insulin_DF["Time"].astype(str))
    new_insulin_DF = insulin_DF[['datetime','BWZ Carb Input (grams)']]
    new_insulin_DF = new_insulin_DF[(new_insulin_DF['BWZ Carb Input (grams)'].notna()) & (new_insulin_DF['BWZ Carb Input (grams)']>0) ]
    new_slots = list(new_insulin_DF['datetime'])

    glucose_DF= glucose_DF[::-1]
    glucose_DF['Sensor Glucose (mg/dL)'] = glucose_DF['Sensor Glucose (mg/dL)'].interpolate(method='linear',limit_direction = 'both')
    glucose_DF['datetime'] = pd.to_datetime(glucose_DF["Date"].astype(str) + " " + glucose_DF["Time"].astype(str))
    new_glucose_DF = glucose_DF[['datetime','Sensor Glucose (mg/dL)']]
    
    no_meal_Times =[]    
    no_meal_Times = meal_no_meal_slots(new_slots,pd.Timedelta('0 days 240 min'))
    no_meal_data_DF = get_meal_no_meal_data_DF(no_meal_Times,2,4,False,new_glucose_DF)
    no_meal_data_DFFeatures = glucoseFeatures(no_meal_data_DF)
    no_meal_standard = standard_scaler.fit_transform(no_meal_data_DFFeatures)
    no_meal_pca = pd.DataFrame(pca.fit_transform(no_meal_standard))
    no_meal_pca['class'] = 0

    meal_Times=[]
    meal_Times = meal_no_meal_slots(new_slots,pd.Timedelta('0 days 120 min'))
    meal_data_DF = get_meal_no_meal_data_DF(meal_Times,-0.5,2,True,new_glucose_DF)
    meal_data_DFFeatures = glucoseFeatures(meal_data_DF)
    meal_standard = standard_scaler.fit_transform(meal_data_DFFeatures)
    pca.fit(meal_standard)
    meal_pca = pd.DataFrame(pca.fit_transform(meal_standard))
    meal_pca['class'] = 1
        
    data = meal_pca.append(no_meal_pca)
    data.index = [i for i in range(data.shape[0])]
    return data



def root_mean_square(row):
    root_mean_square = 0
    for p in range(0, len(row) - 1):
        root_mean_square = root_mean_square + np.square(row[p])
    return np.sqrt(root_mean_square / len(row))

def glucoseEntropy(row):
    row_length = len(row)
    entropy = 0
    if row_length <= 1:
        return 0
    else:
        value, count = np.unique(row, return_counts=True)
        ratio = count / row_length
        non_zero_ratio = np.count_nonzero(ratio)
        if non_zero_ratio <= 1:
            return 0
        for i in ratio:
            entropy -= i * np.log2(i)
        return entropy

def absolute_value_mean(row):
    mean_val = 0
    for p in range(0, len(row) - 1):
        mean_val = mean_val + np.abs(row[(p + 1)] - row[p])
    return mean_val / len(row)

def FFT(row):
    FFT = fft(row)
    row_length = len(row)
    amplitude = []
    frequency = np.linspace(0, row_length * 2/300, row_length)
    for amp in FFT:
        amplitude.append(np.abs(amp))
    sorted_amplitude = amplitude
    sorted_amplitude = sorted(sorted_amplitude)
    max_amplitude = sorted_amplitude[(-2)]
    max_frequency = frequency.tolist()[amplitude.index(max_amplitude)]
    return [max_amplitude, max_frequency]

def glucoseFeatures(meal_no_meal_DF):
    glucose_features=pd.DataFrame()
    for i in range(0, meal_no_meal_DF.shape[0]):
        row = meal_no_meal_DF.iloc[i, :].tolist()
        glucose_features = glucose_features.append({ 
         'root_mean_square':root_mean_square(row),
         'glucoseEntropy':glucoseEntropy(row),
         'min':min(row), 
         'max':max(row),
         'range': max(row) - min(row),
         'absolute_value_mean1':absolute_value_mean(row[:13]), 
         'absolute_value_mean2':absolute_value_mean(row[13:]),  
         'FFT1':FFT(row[:13])[0], 
         'FFT2':FFT(row[:13])[1], 
         'FFT3':FFT(row[13:])[0], 
         'FFT4':FFT(row[13:])[1]},
          ignore_index=True)
    return glucose_features
  
if __name__=='__main__':
    insulin_DF=pd.read_csv("InsulinData.csv",low_memory=False)
    glucose_DF=pd.read_csv("CGMData.csv",low_memory=False)
    insulin_DF_1=pd.read_csv("Insulin_patient2.csv",low_memory=False)
    glucose_DF_1=pd.read_csv("CGM_patient2.csv",low_memory=False)
    
    insulin_data=pd.concat([insulin_DF_1,insulin_DF])
    glucose_data=pd.concat([glucose_DF_1,glucose_DF])
    
    data= meal_no_meal_data(insulin_data,glucose_data)
    x = data.iloc[:, :-1]
    y = data.iloc[:, -1]
    
    # define the model
    # model = svm.SVC(kernel='linear', C=0.1, gamma=0.1)
    # model = XGBClassifier()
    model = HistGradientBoostingClassifier(max_iter=100)

    # define the k-fold cross-validation iterator
    kfold = model_selection.KFold(n_splits=10, shuffle=True, random_state=1)

    # initialize empty lists to store evaluation metrics
    acc_scores, prec_scores, rec_scores, f1_scores = [], [], [], []

    # loop over the folds
    for train, test in kfold.split(x, y):
        x_train, x_test = x.iloc[train], x.iloc[test]
        y_train, y_test = y.iloc[train], y.iloc[test]

        # fit the model on the training data
        model.fit(x_train, y_train)

        # make predictions on the test data
        y_pred = model.predict(x_test)

        # calculate and append evaluation metrics for this fold
        acc_scores.append(metrics.accuracy_score(y_test, y_pred))
        prec_scores.append(metrics.precision_score(y_test, y_pred))
        rec_scores.append(metrics.recall_score(y_test, y_pred))
        f1_scores.append(metrics.f1_score(y_test, y_pred))

    # print the mean and standard deviation of each evaluation metric across all folds
    print(f"Accuracy: {round(np.mean(acc_scores), 2)}")
    print(f"Precision: {round(np.mean(prec_scores), 2)}")
    print(f"Recall: {round(np.mean(rec_scores), 2)}")
    print(f"F1 Score: {round(np.mean(f1_scores), 2)}")

    with open('model.pkl', 'wb') as (file):
        pickle.dump(model, file)
