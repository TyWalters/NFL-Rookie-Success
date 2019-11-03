# coding: utf-8

# packages needed
import pandas as pd
import numpy as np
from fancyimpute import KNN
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
from sklearn.metrics import mean_squared_error
from sklearn.linear_model import Ridge
from sklearn.linear_model import Lasso
from sklearn.linear_model import ElasticNet
from sklearn.neighbors import KNeighborsRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor
import os

file_path = os.path.dirname(os.path.abspath("__file__"))

df = pd.read_csv(file_path + "\\player_bio.csv", encoding="utf-8")

stats = pd.read_csv(file_path + "\\player_nfl_stats.csv", encoding="utf-8")

college_stats = pd.read_csv(file_path + "\\player_college_stats.csv", encoding="utf-8")

# applying season ranks by position and points
# stats['rank'] = stats.groupby(['season', 'position']).points.rank(method='dense', ascending=False)

def q25(x):
    return x.quantile(0.25)

def q75(x):
    return x.quantile(0.75)

print(df[(df.pick.isnull() == True) & (df.draft_year1.isnull() == False)])

college_stats['college_points'] = college_stats.pass_yards * 0.04 + college_stats.pass_td * 4 + (college_stats.intcp * -2) + ((college_stats.rush_yards + college_stats.rec_yards) * 0.10) + ((college_stats.rush_td + college_stats.rec_td) * 6) + college_stats.rec * 0.5

# college_summary = college_stats.groupby("college_pid").agg(['count', 'sum', 'mean', 'first',
#                                                             'last', 'max', 'min', 'median']).reset_index()
college_trend = college_stats.groupby('college_pid')['college_points'].apply(lambda x: 
                                                           x.diff().mean()).reset_index(name='avg_diff').fillna(0)

college_summary = college_stats.groupby("college_pid").mean().reset_index()
college_summary = college_summary.merge(college_trend, on='college_pid')

# college_summary.columns = college_summary.columns.map('_'.join).str.strip('_')
df['draft_year'].fillna(df['draft_year1'], inplace=True)
df['position'].fillna(df['position1'], inplace=True)

# merge and drop players without combine data or without any stats
stats = stats.merge(df[['player_id', 'draft_year']], on='player_id', how='outer')

# remove all seasons except first four
stats = stats[(stats.season - stats.draft_year) < 4]

# summary_stats = stats.groupby("player_id").agg(['count', 'sum', 'mean', 'std', 'first', 'last', 'max', 'min', q25, 'median',
#                                 q75])['points'].reset_index()
summary_stats = stats.groupby("player_id").mean()['points'].reset_index()

all_data = summary_stats.merge(df, on='player_id', how='inner').merge(college_summary, on='college_pid', how='inner')

all_data = all_data[all_data.name != "Dan Vitale"]

all_data['birth_year'] = [x[0:4] for x in all_data.birth_date.astype(str)]
all_data['age'] = all_data.draft_year - all_data.birth_year.astype(int)

# replace missing combine values with null for imputing
all_data.arm_length.replace(0, np.nan, inplace=True)
all_data.hand_size.replace(0, np.nan, inplace=True)
all_data.front_shoulder.replace(0, np.nan, inplace=True)
all_data.back_shoulder.replace(0, np.nan, inplace=True)
all_data.wonderlic.replace(0, np.nan, inplace=True)
all_data.pass_velocity.replace(0, np.nan, inplace=True)
all_data.ten_yard.replace(0, np.nan, inplace=True)
all_data.twenty_yard.replace(0, np.nan, inplace=True)
all_data.forty_yard.replace(0, np.nan, inplace=True)
all_data.bench_press.replace(0, np.nan, inplace=True)
all_data.vertical_leap.replace(0, np.nan, inplace=True)
all_data.broad_jump.replace(0, np.nan, inplace=True)
all_data.shuttle.replace(0, np.nan, inplace=True)
all_data.sixty_shuttle.replace(0, np.nan, inplace=True)
all_data.three_cone.replace(0, np.nan, inplace=True)
all_data.four_square.replace(0, np.nan, inplace=True)

imp_columns = ['round', 'pick', 'height', 'weight', 'bmi', 'arm_length', 'hand_size', 'front_shoulder', 'back_shoulder',
'wonderlic', 'pass_velocity', 'ten_yard', 'twenty_yard', 'forty_yard', 'bench_press', 'vertical_leap', 'broad_jump',
'shuttle', 'sixty_shuttle', 'three_cone', 'four_square', 'games', 'cmp', 'pass_att', 'pass_yards', 'pass_td', 'intcp',
'rating', 'rush_att', 'rush_yards', 'rush_td', 'rec', 'rec_yards', 'rec_td', 'college_points', 'avg_diff', 'age']

imp_numeric = all_data[['round', 'pick', 'height', 'weight', 'bmi', 'arm_length', 'hand_size', 'front_shoulder',
'back_shoulder', 'wonderlic', 'pass_velocity', 'ten_yard', 'twenty_yard', 'forty_yard', 'bench_press', 'vertical_leap', 
'broad_jump', 'shuttle', 'sixty_shuttle', 'three_cone', 'four_square', 'games', 'cmp', 'pass_att', 'pass_yards', 'pass_td', 
'intcp', 'rating', 'rush_att', 'rush_yards', 'rush_td', 'rec', 'rec_yards', 'rec_td', 'college_points', 
                        'avg_diff', 'age']].values

# KNN imputing
imp = pd.DataFrame(KNN(k=5).fit_transform(imp_numeric), columns=imp_columns)

# add imputed values rest of dataset
all_data_imp = all_data.drop(imp_columns, axis=1)

master_data = all_data_imp.merge(imp, left_index=True, right_index=True)

# new combine variables
master_data['speed_score'] = (master_data.weight * 200)/(master_data.forty_yard**4)
master_data['agility_score'] = master_data.three_cone + master_data.shuttle
master_data['height_adj_ss'] = master_data.speed_score * (master_data.height / 73.5) ** 1.5
master_data['burst_score'] = master_data.vertical_leap + master_data.broad_jump
# catch radius and weight adjusted bench ?

wr_data = master_data[master_data.position == 'WR']
rb_data = master_data[master_data.position == 'RB']
te_data = master_data[master_data.position == 'TE']
qb_data = master_data[master_data.position == 'QB']


# 'count', 'sum', 'mean', 'std', 'first', 'last', 'max', 'min', 'median'


wr_data = wr_data[['player_id', 'points', 'college_pid', 'name', 'birth_year', 'birth_date', 'draft_year', 'age', 'round', 
'pick', 'position', 'height', 'weight', 'bmi', 'arm_length', 'hand_size', 'front_shoulder', 'back_shoulder', 'wonderlic',
'ten_yard', 'twenty_yard', 'forty_yard', 'bench_press', 'vertical_leap', 'broad_jump', 'shuttle', 'sixty_shuttle', 'three_cone',
'four_square', 'speed_score', 'agility_score', 'burst_score',  'height_adj_ss', 'games', 'rec', 'rec_yards', 'rec_td', 
                   'college_points', 'avg_diff']]

te_data = te_data[['player_id', 'points', 'college_pid', 'name', 'birth_year', 'birth_date', 'draft_year', 'age', 'round', 
'pick', 'position', 'height', 'weight', 'bmi', 'arm_length', 'hand_size', 'front_shoulder', 'back_shoulder', 'wonderlic',
'ten_yard', 'twenty_yard', 'forty_yard', 'bench_press', 'vertical_leap', 'broad_jump', 'shuttle', 'sixty_shuttle', 'three_cone',
'four_square', 'speed_score', 'agility_score', 'burst_score',  'height_adj_ss', 'games', 'rec', 'rec_yards', 'rec_td',
                   'college_points', 'avg_diff']]

rb_data = rb_data[['player_id', 'points', 'college_pid', 'name', 'birth_year', 'birth_date', 'draft_year', 'age', 'round', 
'pick', 'position', 'height', 'weight', 'bmi', 'arm_length', 'hand_size', 'front_shoulder', 'back_shoulder', 'wonderlic',
'ten_yard', 'twenty_yard', 'forty_yard', 'bench_press', 'vertical_leap', 'broad_jump', 'shuttle', 'sixty_shuttle', 'three_cone',
'four_square', 'speed_score', 'agility_score', 'burst_score',  'height_adj_ss', 'games', 'rush_att', 'rush_yards', 'rush_td',
'rec', 'rec_yards', 'rec_td', 'college_points', 'avg_diff']]

qb_data = qb_data[['player_id', 'points', 'college_pid', 'name', 'birth_year', 'birth_date', 'draft_year', 'age', 'round', 
'pick', 'position', 'height', 'weight', 'bmi', 'arm_length', 'hand_size', 'front_shoulder', 'back_shoulder', 'wonderlic',
'pass_velocity', 'ten_yard', 'twenty_yard', 'forty_yard', 'bench_press', 'vertical_leap', 'broad_jump', 'shuttle',
'sixty_shuttle', 'three_cone', 'four_square', 'speed_score', 'agility_score', 'burst_score',  'height_adj_ss', 'games', 
'cmp', 'pass_att', 'pass_yards', 'pass_td', 'intcp', 'rating', 'rush_att', 'rush_yards', 'rush_td', 'college_points', 
                   'avg_diff']]


# qb_data.corr()[['points']].transpose().to_csv('QBCorr.csv')

# rb_data.corr()[['points']].transpose().to_csv('RBCorr.csv')

# wr_data.corr()[['points']].transpose().to_csv('WRCorr.csv')

# te_data.corr()[['points']].transpose().to_csv('TECorr.csv')

# qb_data.to_csv('QBPlayerData.csv')
# rb_data.to_csv('RBPlayerData.csv')
# wr_data.to_csv('WRPlayerData.csv')
# te_data.to_csv('TEPlayerData.csv')
# master_data.to_csv('NFLPlayerData.csv', 
#                 index=False)


X = qb_data[['age','pick', 'height', 'weight', 'bmi', 'arm_length', 'hand_size', 'front_shoulder', 'back_shoulder',
'wonderlic', 'pass_velocity', 'shuttle', 'sixty_shuttle', 'three_cone', 'four_square', 'speed_score', 'agility_score',
'burst_score',  'height_adj_ss', 'cmp', 'pass_att', 'pass_yards', 'pass_td', 'rush_att',
'rush_yards', 'rush_td', 'avg_diff']]

y = qb_data['points']

#X = rb_data[['age', 'pick', 'height', 'weight', 'bmi', 'arm_length', 'hand_size', 'front_shoulder', 'back_shoulder', 'wonderlic',
#'ten_yard', 'twenty_yard', 'forty_yard', 'bench_press', 'vertical_leap', 'broad_jump', 'shuttle', 'sixty_shuttle', 'three_cone',
#'four_square', 'speed_score', 'agility_score', 'burst_score',  'height_adj_ss', 'games', 'rush_att', 'rush_yards', 'rush_td',
#'rec', 'rec_yards', 'rec_td', 'college_points', 'avg_diff']]
#
#y = rb_data['points']
#
#
#y = wr_data['points']
#
#X = wr_data[['age', 'pick', 'height', 'weight', 'bmi', 'arm_length', 'hand_size', 'front_shoulder', 'back_shoulder', 'wonderlic',
#'ten_yard', 'twenty_yard', 'forty_yard', 'bench_press', 'vertical_leap', 'broad_jump', 'shuttle', 'sixty_shuttle', 'three_cone',
#'four_square', 'speed_score', 'agility_score', 'burst_score',  'height_adj_ss', 'games', 'rec', 'rec_yards', 'rec_td', 
#                   'college_points', 'avg_diff']]
#
#
#y = te_data['points']
#
#X = te_data[['age', 'pick', 'height', 'weight', 'bmi', 'arm_length', 'hand_size', 'front_shoulder', 'back_shoulder', 'wonderlic',
#'ten_yard', 'twenty_yard', 'forty_yard', 'bench_press', 'vertical_leap', 'broad_jump', 'shuttle', 'sixty_shuttle', 'three_cone',
#'four_square', 'speed_score', 'agility_score', 'burst_score',  'height_adj_ss', 'games', 'rec', 'rec_yards', 'rec_td',
#                   'college_points', 'avg_diff']]


X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=42)

# model = LinearRegression()
dt = DecisionTreeRegressor()
model = RandomForestRegressor(n_estimators=500, oob_score=True, random_state=100)
model.fit(X_train, y_train)

# predict probabilities
predicted = model.predict(X_test)

print(mean_squared_error(y_test, predicted))

print(r2_score(y_test, predicted))

# pd.DataFrame(model.coef_, X.columns, columns=['Coefficient']) 
