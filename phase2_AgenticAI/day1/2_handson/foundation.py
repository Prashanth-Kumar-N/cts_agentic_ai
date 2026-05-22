import pandas as pd
from sklearn.model_selection import train_test_split
import statsmodels.api as sm

file="D:/stackroute/2_AI-assisted-programming/learning_requirements/cognizant/2025/1/code/2_AgenticAI/dataset/2_fraud.csv"

data = pd.read_csv(file)

# this will give the 0 and 1 count
data.is_fraud.value_counts()


data.dtypes

# categorical columns
fc = list(data.select_dtypes(include=['object', 'category']).columns.values)
print(fc)

# fc.remove('transaction_id')
# fc.remove('customer_id')
# fc.remove('txn_timestamp')

cols_to_remove = ['transaction_id', 'customer_id', 'txn_timestamp']
for c in cols_to_remove:
    fc.remove(c)
print(fc)

data.device_type.unique()

# conver the FC into a numerical representation
# One Hot Encoding

# make dummy variables for all the Categorical variables
new_data = data.copy()
for c in fc:
    dummy = pd.get_dummies(new_data[c], drop_first=True, prefix=c)
    new_data = new_data.join(dummy)

print(new_data.dtypes)

# remove all the old FC
new_data.drop(columns=fc,inplace=True)

print(new_data.dtypes)

# Boolean columns, if any, should be converted to Integer/Float
bc = new_data.select_dtypes(include=['bool']).columns
if len(bc) > 0:
    new_data[bc] = new_data[bc].astype(int)

Y = "is_fraud"

trainx,testx,trainy,testy = train_test_split(new_data.drop(Y,axis=1), new_data[Y], test_size=0.1)

# 90% of the actual data == Train data
print(trainx.shape)
print(trainy.shape)

# 10% of the actual data == Test data
print(testx.shape)
print(testy.shape)

trainx.head(1)
trainy.head(1)

testx.head(1)
testy.head(1)

# Build the Classification Model
# Logistic Regression

#
trainx.drop(columns=cols_to_remove,inplace=True)
testx.drop(columns=cols_to_remove,inplace=True)

model = sm.Logit(trainy,trainx).fit()

# Predict the Model on the Test Data
p1 = model.predict(testx)
print(p1[:10])
# -----------------------------------------------

from sklearn.feature_selection import f_classif, SelectFdr

# f_statistic, pvalue = f_classif(trainx,trainy)
# df_fstats = pd.DataFrame({"feature":trainx.columns, "fstat":f_statistic,"pvalue":pvalue })
# print(df_fstats)

selector = SelectFdr(score_func=f_classif, alpha=0.05)
selector.fit_transform(trainx, trainy)

# get_support() --> automatically identifies which features are significant based on the F-Score.

df_fdr = pd.DataFrame({"feature": trainx.columns, "f_score": selector.scores_, "p_value": selector.pvalues_,  "selected": selector.get_support()})

df_fdr = df_fdr.sort_values("selected", ascending=False)

print(df_fdr)


