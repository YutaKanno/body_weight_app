import pandas as pd
import numpy as np
import streamlit as st
from plotnine import *


# ============================================
# 📝 prepare data for streamlit app
# ============================================

def load_spreadsheet():
    url = "https://docs.google.com/spreadsheets/d/1VypMFcyfyUnyjCwIqJClsg2Bkpbwx8UrvmDG_tPt9Nw/export?format=csv"
    df  = pd.read_csv(url)
    return df


def process_data(df):
    df = df.copy()
    
    # convert to float
    df['体重(kg)'] = pd.to_numeric(df['体重(kg)'], errors='coerce')
    df['体脂肪率(%)'] = pd.to_numeric(df['体脂肪率(%)'], errors='coerce')
    df = df.dropna()

    # add column
    df['除脂肪体重(kg)'] = round(df['体重(kg)'] * (1 - df['体脂肪率(%)'] / 100), 1)
    df['日付'] = pd.to_datetime(df['タイムスタンプ'].str.split(' ').str[0], format='%Y/%m/%d') 
    
    # add column for difference
    df = df.sort_values(by=['氏名', '日付'])
    df['体重(kg)_diff'] = df.groupby('氏名')['体重(kg)'].diff()
    df['体脂肪率(%)_diff'] = df.groupby('氏名')['体脂肪率(%)'].diff()
    df['除脂肪体重(kg)_diff'] = df.groupby('氏名')['除脂肪体重(kg)'].diff()
    
    df[['体重(kg)_diff', '体脂肪率(%)_diff', '除脂肪体重(kg)_diff']] = df[['体重(kg)_diff', '体脂肪率(%)_diff', '除脂肪体重(kg)_diff']].fillna(0)
    df[['体重(kg)_diff', '体脂肪率(%)_diff', '除脂肪体重(kg)_diff']] = df[['体重(kg)_diff', '体脂肪率(%)_diff', '除脂肪体重(kg)_diff']].astype(float)

    return df


def indiv_data(df, name):
    df = df.copy()
    
    df = df[df['氏名'] == name]
    df = df.sort_values(by='日付', ascending=False)
    
    return df[['日付', '体重(kg)', '体脂肪率(%)', '除脂肪体重(kg)']]


def indiv_data_newest(df, name):
    df = df.copy()
    
    df = df[df['氏名'] == name]
    df = df.sort_values(by='日付', ascending=False)
    df = df.iloc[0]
    
    result = {
        '日付': df['日付'].strftime('%Y/%m/%d'),
        '体重(kg)': {
            'value': round(df['体重(kg)'], 1),
            'delta': round(df['体重(kg)_diff'], 1)
        },
        '体脂肪率(%)': {
            'value': round(df['体脂肪率(%)'], 1),
            'delta': round(df['体脂肪率(%)_diff'], 1)
        },
        '除脂肪体重(kg)': {
            'value': round(df['除脂肪体重(kg)'], 1),
            'delta': round(df['除脂肪体重(kg)_diff'], 1)
        }
    }
    
    return result
    

def plot_indiv_line(df, name, item):
    df       = df.copy()
    indiv_df = indiv_data(df, name)
    
    p = (
        ggplot(indiv_df, aes(x='日付', y=item))
        + geom_line(color='blue')
        + geom_point(size=5)
        + labs(title='', x='', y='')
        + theme_minimal()
    )
    
    return p
    
    
# ============================================
# 📝 createstreamlit app
# ============================================
def create_streamlit_app(df):
    st.title('Tsukuba 体重管理システム')
    st.write(f'最終データ更新日時: {df["日付"].max().strftime("%Y/%m/%d")}')
    st.write('入力フォーム:')
    st.write('https://docs.google.com/forms/d/e/1FAIpQLSeW-O61nAJtWq8AqKAQX_VX4RBI8Bnc1Wt2UgklxJGZlnSMCg/viewform?usp=sharing&ouid=113534825337596739095')

    st.write('---')
    
    selected_name = st.selectbox('氏名を選択', df['氏名'].unique())
    newest_data = indiv_data_newest(df, selected_name)
    
    st.write('---')
    
    st.write(f'## {selected_name} 最新データ')
    st.write(f'**測定日:** {newest_data["日付"]}')
    
    # 3つのカラムに分けて表示
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="体重",
            value=f"{newest_data['体重(kg)']['value']:.1f} kg",
            delta=f"{newest_data['体重(kg)']['delta']:+.1f} kg" if newest_data['体重(kg)']['delta'] != 0 else None
        )
    
    with col2:
        st.metric(
            label="体脂肪率",
            value=f"{newest_data['体脂肪率(%)']['value']:.1f} %",
            delta=f"{newest_data['体脂肪率(%)']['delta']:+.1f} %" if newest_data['体脂肪率(%)']['delta'] != 0 else None
        )
    
    with col3:
        st.metric(
            label="除脂肪体重",
            value=f"{newest_data['除脂肪体重(kg)']['value']:.1f} kg",
            delta=f"{newest_data['除脂肪体重(kg)']['delta']:+.1f} kg" if newest_data['除脂肪体重(kg)']['delta'] != 0 else None
        )
    
    st.write('---')
    
    plot_columns = ['体重(kg)', '体脂肪率(%)', '除脂肪体重(kg)']
    for column in plot_columns:
        st.write(f'## {column} 推移グラフ')
        plot = plot_indiv_line(df, selected_name, column)
        st.pyplot(plot.draw())
        
        st.write('---')
    
    st.write('## 個人データ')
    indiv_df = indiv_data(df, selected_name)
    st.dataframe(indiv_df)




if __name__ == '__main__':
    df = load_spreadsheet()
    df = process_data(df)
    create_streamlit_app(df)