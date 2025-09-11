import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import platform
import os

# 한글 폰트 설정 (Mac, Windows 자동 감지)
if platform.system() == 'Darwin': # Mac
    plt.rc('font', family='AppleGothic')
elif platform.system() == 'Windows': # Windows
    plt.rc('font', family='Malgun Gothic')

plt.rcParams['axes.unicode_minus'] = False # 마이너스 폰트 깨짐 방지


# 데이터 로딩 함수 (에러 처리 강화)
@st.cache_data
def load_data():
    #file_path = 'crime_anal_merged.csv'
    # dataBoard라는 하위 디렉토리에 코드를 업로드 했으므로 상대경로 사용하는것으로 변경
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'crime_anal_merged.csv')
    try:
        # utf-8 인코딩으로 먼저 시도
        data = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            # utf-8 실패 시 cp949(Windows 기본 한글 인코딩)로 재시도
            data = pd.read_csv(file_path, encoding='cp949')
        except Exception as e:
            st.error(f"파일 인코딩 문제일 수 있습니다. 파일을 읽는 중 에러가 발생했습니다: {e}")
            return None
    except FileNotFoundError:
        st.error(f"'{file_path}' 파일을 찾을 수 없습니다. 'app.py'와 동일한 폴더에 파일이 있는지 확인해주세요.")
        return None
    except Exception as e:
        st.error(f"데이터를 로드하는 중 예상치 못한 에러가 발생했습니다: {e}")
        return None

    # 안정적인 처리를 위해 컬럼명을 공백 없는 영문으로 변경
    # 원본 파일 컬럼명: '살인 발생' -> 변경 후: 'Murder_Occurrence'
    new_columns = {
        '구별': 'District', '관서명': 'Office', '살인 발생': 'Murder_Occurrence',
        '살인 검거': 'Murder_Arrest', '강도 발생': 'Robbery_Occurrence', '강도 검거': 'Robbery_Arrest',
        '강간 발생': 'Rape_Occurrence', '강간 검거': 'Rape_Arrest', '절도 발생': 'Theft_Occurrence',
        '절도 검거': 'Theft_Arrest', '폭력 발생': 'Violence_Occurrence', '폭력 검거': 'Violence_Arrest',
        '총 발생 건수': 'Total_Crimes', 'CCTV 총계': 'CCTV_Total', 'CCTV 최근증가율': 'CCTV_Recent_Increase_Rate',
        '총인구': 'Total_Population', '한국인': 'Korean_Population', '외국인': 'Foreigner_Population',
        '고령자': 'Elderly_Population', '인구 10만명당 범죄율': 'Crime_Rate_per_100k'
    }
    data.rename(columns=new_columns, inplace=True)

    # 필수 컬럼 존재 여부 확인
    required_cols = list(new_columns.values())
    if not all(col in data.columns for col in required_cols):
        st.error("CSV 파일의 컬럼명이 예상과 다릅니다. 원본 파일의 컬럼을 확인해주세요.")
        st.write("현재 파일의 컬럼:", data.columns.tolist())
        return None

    return data


df = load_data()

# 데이터가 성공적으로 로드된 경우에만 대시보드 표시
if df is not None:
    # 서울 자치구별 위도, 경도 데이터
    geo_data = {
        '강남구': [37.4979, 127.0276], '강동구': [37.5301, 127.1238], '강북구': [37.6396, 127.0257],
        '강서구': [37.5509, 126.8495], '관악구': [37.4784, 126.9516], '광진구': [37.5385, 127.0824],
        '구로구': [37.4954, 126.8875], '금천구': [37.4519, 126.9023], '노원구': [37.6542, 127.0568],
        '도봉구': [37.6688, 127.0471], '동대문구': [37.5744, 127.0397], '동작구': [37.5124, 126.9393],
        '마포구': [37.5662, 126.9016], '서대문구': [37.5791, 126.9368], '서초구': [37.4837, 127.0324],
        '성동구': [37.5635, 127.0368], '성북구': [37.5894, 127.0167], '송파구': [37.5145, 127.1058],
        '양천구': [37.5169, 126.8664], '영등포구': [37.5264, 126.8963], '용산구': [37.5325, 126.9900],
        '은평구': [37.6027, 126.9291], '종로구': [37.5730, 126.9794], '중구': [37.5639, 126.9975],
        '중랑구': [37.6065, 127.0926]
    }
    df['Latitude'] = df['District'].map(lambda x: geo_data.get(x, [None, None])[0])
    df['Longitude'] = df['District'].map(lambda x: geo_data.get(x, [None, None])[1])

    # --- 대시보드 UI ---
    st.title('🚨 서울시 범죄 현황 분석 대시보드')
    st.markdown("""
    이 대시보드는 서울시 자치구별 범죄 현황 데이터를 시각화하여 보여줍니다.
    다양한 인터랙티브 차트를 통해 데이터를 탐색하고 인사이트를 얻어보세요.
    """)

    # --- 데이터 개요 ---
    st.header('📊 데이터 개요')
    st.dataframe(df.head())
    st.markdown(f"**전체 데이터 수:** {df.shape[0]}개 자치구")

    # --- 시각화 ---
    st.header('📈 인터랙티브 시각화')

    # 1. 자치구별 범죄 발생 현황 (바 차트)
    st.subheader('자치구별 범죄 발생 현황')
    crime_type_map = {
        '총 발생 건수': 'Total_Crimes', '살인': 'Murder_Occurrence', '강도': 'Robbery_Occurrence',
        '강간': 'Rape_Occurrence', '절도': 'Theft_Occurrence', '폭력': 'Violence_Occurrence'
    }
    crime_type_display = st.selectbox(
        '범죄 유형을 선택하세요.', list(crime_type_map.keys()), key='crime_type_bar'
    )
    crime_col = crime_type_map[crime_type_display]

    sorted_df = df.sort_values(by=crime_col, ascending=False)
    fig_bar = px.bar(
        sorted_df, x='District', y=crime_col, title=f'자치구별 {crime_type_display} 발생 건수',
        labels={'District': '자치구', crime_col: '발생 건수'}, height=500
    )
    fig_bar.update_layout(xaxis={'categoryorder':'total descending'})
    st.plotly_chart(fig_bar, use_container_width=True)

    # 2. 변수 간 상관관계 (산점도)
    st.subheader('변수 간 상관관계 분석')
    numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    
    default_x_index = numeric_columns.index('CCTV_Total') if 'CCTV_Total' in numeric_columns else 0
    default_y_index = numeric_columns.index('Crime_Rate_per_100k') if 'Crime_Rate_per_100k' in numeric_columns else 1

    x_axis = st.selectbox('X축 데이터를 선택하세요.', numeric_columns, index=default_x_index)
    y_axis = st.selectbox('Y축 데이터를 선택하세요.', numeric_columns, index=default_y_index)

    fig_scatter = px.scatter(
        df, x=x_axis, y=y_axis, color='District', hover_name='District',
        title=f'{x_axis}와(과) {y_axis}의 상관관계', height=600
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    # 3. 데이터 상관관계 히트맵
    st.subheader('데이터 상관관계 히트맵')
    numeric_df = df[numeric_columns]
    corr = numeric_df.corr()

    fig_heatmap, ax = plt.subplots(figsize=(12, 10))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap='coolwarm', ax=ax)
    ax.set_title('상관관계 히트맵')
    st.pyplot(fig_heatmap)


    # 4. 지도 시각화
    st.subheader('🗺️ 자치구별 범죄율 지도')
    m = folium.Map(location=[37.5665, 126.9780], zoom_start=11)

    for idx, row in df.iterrows():
        if pd.notna(row['Latitude']) and pd.notna(row['Longitude']):
            folium.CircleMarker(
                location=[row['Latitude'], row['Longitude']],
                radius=row['Crime_Rate_per_100k'] / 100,
                popup=f"<strong>{row['District']}</strong><br>인구 10만명당 범죄율: {row['Crime_Rate_per_100k']:.2f}",
                color='#E31A1C', fill=True, fill_color='#E31A1C'
            ).add_to(m)

    st_folium(m, width=725, height=500)
