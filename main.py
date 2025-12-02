import pandas as pd
import numpy as np
import streamlit as st
from plotnine import *


# ============================================
# 📝 prepare data for streamlit app
# ============================================

@st.cache_data(ttl=60)  # 60秒ごとにキャッシュを更新
def load_spreadsheet():
    # スプレッドシートID
    spreadsheet_id = "1UCfJSF0MUqtFxLBncU93D3FToA8Zued25wY02u2LdLo"
    
    # まずgidなしで試す（最初のシートを読み込む）
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv"
    
    try:
        df = pd.read_csv(url)
        return df
    except Exception as e:
        # gidなしで失敗した場合、gidを指定して再試行
        st.warning(f"gidなしでの読み込みに失敗しました。gidを指定して再試行します。エラー: {e}")
        url_with_gid = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid=1918564041"
        try:
            df = pd.read_csv(url_with_gid)
            return df
        except Exception as e2:
            st.error(f"スプレッドシートの読み込みに失敗しました: {e2}")
            st.info("以下の点を確認してください:")
            st.info("1. スプレッドシートが「リンクを知っている全員」に公開されているか")
            st.info("2. スプレッドシートIDが正しいか")
            st.info("3. 正しいシート（タブ）のgidを指定しているか")
            raise


def process_data(df):
    df = df.copy()
    
    # convert to float
    df['身長 (m)'] = pd.to_numeric(df['身長 (cm)'], errors='coerce') / 100
    df['体重 (kg)'] = pd.to_numeric(df['体重 (kg)'], errors='coerce')
    df['体脂肪率 (%)'] = pd.to_numeric(df['体脂肪率 (%)'], errors='coerce')
    df = df.dropna(subset=['身長 (cm)', '体重 (kg)', '体脂肪率 (%)'])

    # add column
    df['除脂肪体重 (kg)'] = round(df['体重 (kg)'] * (1 - df['体脂肪率 (%)'] / 100), 1)
    df['FFMI'] = round(df['除脂肪体重 (kg)'] / df['身長 (m)'] ** 2, 2)
    df['日付'] = pd.to_datetime(df['タイムスタンプ'].str.split(' ').str[0], format='%Y/%m/%d') 
    
    # add column for difference
    df = df.sort_values(by=['氏名 (姓名間空けない)', '日付'])
    df['体重 (kg)_diff'] = df.groupby('氏名 (姓名間空けない)')['体重 (kg)'].diff()
    df['体脂肪率 (%)_diff'] = df.groupby('氏名 (姓名間空けない)')['体脂肪率 (%)'].diff()
    df['除脂肪体重 (kg)_diff'] = df.groupby('氏名 (姓名間空けない)')['除脂肪体重 (kg)'].diff()
    df['FFMI_diff'] = df.groupby('氏名 (姓名間空けない)')['FFMI'].diff()
    
    df[['体重 (kg)_diff', '体脂肪率 (%)_diff', '除脂肪体重 (kg)_diff', 'FFMI_diff']] = df[['体重 (kg)_diff', '体脂肪率 (%)_diff', '除脂肪体重 (kg)_diff', 'FFMI_diff']].fillna(0)
    df[['体重 (kg)_diff', '体脂肪率 (%)_diff', '除脂肪体重 (kg)_diff', 'FFMI_diff']] = df[['体重 (kg)_diff', '体脂肪率 (%)_diff', '除脂肪体重 (kg)_diff', 'FFMI_diff']].astype(float)

    return df


def indiv_data(df, name):
    df = df.copy()
    
    df = df[df['氏名 (姓名間空けない)'] == name]
    df = df.sort_values(by='日付', ascending=False)
    
    return df[['日付', '体重 (kg)', '体脂肪率 (%)', '除脂肪体重 (kg)', 'FFMI']]


def indiv_data_newest(df, name):
    df = df.copy()
    
    df = df[df['氏名 (姓名間空けない)'] == name]
    df = df.sort_values(by='日付', ascending=False)
    df = df.iloc[0]
    
    result = {
        '日付': df['日付'].strftime('%Y/%m/%d'),
        '体重 (kg)': {
            'value': round(df['体重 (kg)'], 1),
            'delta': round(df['体重 (kg)_diff'], 1)
        },
        '体脂肪率 (%)': {
            'value': round(df['体脂肪率 (%)'], 1),
            'delta': round(df['体脂肪率 (%)_diff'], 1)
        },
        '除脂肪体重 (kg)': {
            'value': round(df['除脂肪体重 (kg)'], 1),
            'delta': round(df['除脂肪体重 (kg)_diff'], 1)
        },
        'FFMI': {
            'value': round(df['FFMI'], 1),
            'delta': round(df['FFMI_diff'], 1)
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
    st.write('https://docs.google.com/forms/d/e/1FAIpQLScfuqIiBQ_GNexa2OsS-MS19ZuO1tb55jyWhVYdQYYI3JYllw/viewform?usp=dialog')

    st.write('---')
    
    selected_name = st.selectbox('氏名を選択', df['氏名 (姓名間空けない)'].unique())
    newest_data = indiv_data_newest(df, selected_name)
    
    st.write('---')
    
    st.write(f'## {selected_name} 最新データ')
    st.write(f'**測定日:** {newest_data["日付"]}')
    
    # 3つのカラムに分けて表示
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="体重",
            value=f"{newest_data['体重 (kg)']['value']:.1f} kg",
            delta=f"{newest_data['体重 (kg)']['delta']:+.1f} kg" if newest_data['体重 (kg)']['delta'] != 0 else None
        )
    
    with col2:
        st.metric(
            label="体脂肪率",
            value=f"{newest_data['体脂肪率 (%)']['value']:.1f} %",
            delta=f"{newest_data['体脂肪率 (%)']['delta']:+.1f} %" if newest_data['体脂肪率 (%)']['delta'] != 0 else None
        )
    
    with col3:
        st.metric(
            label="除脂肪体重",
            value=f"{newest_data['除脂肪体重 (kg)']['value']:.1f} kg",
            delta=f"{newest_data['除脂肪体重 (kg)']['delta']:+.1f} kg" if newest_data['除脂肪体重 (kg)']['delta'] != 0 else None
        )
   
    with col4:
        st.metric(
            label="FFMI",
            value=f"{newest_data['FFMI']['value']:.2f}",
            delta=f"{newest_data['FFMI']['delta']:+.2f}" if newest_data['FFMI']['delta'] != 0 else None
        )
    
    st.write('---')
    
    plot_columns = ['体重 (kg)', '体脂肪率 (%)', '除脂肪体重 (kg)', 'FFMI']
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
