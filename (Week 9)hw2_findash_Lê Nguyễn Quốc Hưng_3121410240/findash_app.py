from vnstock import Vnstock
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==================================================================
# HÀM TIỆN ÍCH
# ==================================================================

def get_stock_obj(ticker):
    """Khởi tạo đối tượng cổ phiếu"""
    try:
        return Vnstock().stock(symbol=ticker, source="VCI")
    except Exception as e:
        st.error(f"Lỗi khởi tạo đối tượng cổ phiếu: {e}")
        return None

# ==================================================================
# TAB 1 - Tổng quan
# ==================================================================

def tab1(ticker):
    st.title("Tổng quan")
    st.write(f"Đang hiển thị dữ liệu cho: **{ticker}**")

    if ticker == '-':
        st.info("Vui lòng chọn mã cổ phiếu.")
        return

    stock = get_stock_obj(ticker)
    if not stock:
        return

    # --- Tóm tắt bảng giá ---
    try:
        quote = stock.quote  # <-- Sửa ở đây, không gọi ()
        if isinstance(quote, pd.DataFrame):
            summary_df = quote.T.reset_index()
            summary_df.columns = ["attribute", "value"]

            c1, c2 = st.columns(2)
            with c1:
                st.dataframe(summary_df.iloc[:5])
            with c2:
                st.dataframe(summary_df.iloc[5:])
        else:
            st.warning("Không có dữ liệu bảng giá.")
    except Exception as e:
        st.error(f"Lỗi khi tải bảng giá: {e}")

    # --- Biểu đồ giá lịch sử ---
    @st.cache_data
    def get_price_data(ticker):
        stock = get_stock_obj(ticker)
        df = stock.quote.history(start="2010-01-01", end=datetime.today().strftime("%Y-%m-%d"), interval="1D")
        df["Date"] = pd.to_datetime(df["time"])
        return df.rename(columns={"close": "Close"})

    try:
        df = get_price_data(ticker)
        fig = px.area(df, x="Date", y="Close", title=f"Biểu đồ giá đóng cửa của {ticker}")
        fig.update_xaxes(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1T", step="month", stepmode="backward"),
                    dict(count=3, label="3T", step="month", stepmode="backward"),
                    dict(count=6, label="6T", step="month", stepmode="backward"),
                    dict(count=1, label="1N", step="year", stepmode="backward"),
                    dict(label="Tất cả", step="all")
                ])
            )
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Lỗi khi vẽ biểu đồ: {e}")

# ==================================================================
# TAB 2 - Biểu đồ kỹ thuật
# ==================================================================

def tab2(ticker):
    st.title("Biểu đồ kỹ thuật")
    if ticker == '-':
        st.info("Vui lòng chọn mã cổ phiếu.")
        return

    c1, c2, c3 = st.columns(3)
    with c1:
        start_date = st.date_input("Ngày bắt đầu", datetime.today().date() - timedelta(days=365))
    with c2:
        end_date = st.date_input("Ngày kết thúc", datetime.today().date())
    with c3:
        plot_type = st.selectbox("Loại biểu đồ", ["Line", "Candle"])

    @st.cache_data
    def get_chart_data(ticker, start, end):
        stock = get_stock_obj(ticker)
        df = stock.quote.history(start=start_date.strftime("%Y‑%m‑%d"), end=end_date.strftime("%Y‑%m‑%d"),
                                 interval="1D")
        df["Date"] = pd.to_datetime(df["time"])
        df["SMA_50"] = df["close"].rolling(50).mean()
        return df

    df = get_chart_data(ticker, start_date, end_date)

    if df.empty:
        st.warning("Không có dữ liệu.")
        return

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if plot_type == "Line":
        fig.add_trace(go.Scatter(x=df["Date"], y=df["close"], mode="lines", name="Giá đóng cửa"), secondary_y=False)
    else:
        fig.add_trace(go.Candlestick(x=df["Date"], open=df["open"], high=df["high"],
                                     low=df["low"], close=df["close"], name="Biểu đồ nến"))

    fig.add_trace(go.Scatter(x=df["Date"], y=df["SMA_50"], mode="lines", name="SMA 50 ngày"), secondary_y=False)
    fig.add_trace(go.Bar(x=df["Date"], y=df["volume"], name="Khối lượng"), secondary_y=True)

    fig.update_layout(title=f"Biểu đồ kỹ thuật {ticker}")
    fig.update_yaxes(title_text="Giá (VND)", secondary_y=False)
    fig.update_yaxes(title_text="Khối lượng", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)

# ==================================================================
# TAB 3 - Chỉ số tài chính
# ==================================================================

def tab3(ticker):
    st.title("Các chỉ số tài chính")
    if ticker == '-':
        st.info("Vui lòng chọn mã cổ phiếu.")
        return

    stock = get_stock_obj(ticker)

    @st.cache_data
    @st.cache_data
    def get_financial_ratios(_stock):
        # Lấy 5 năm dữ liệu báo cáo thu nhập, cân đối, lưu chuyển
        yearly_income = _stock.finance.income_statement(period="year", size=5)
        yearly_balance = _stock.finance.balance_sheet(period="year", size=5)
        yearly_cashflow = _stock.finance.cash_flow(period="year", size=5)

        # Tính một số chỉ số cơ bản
        yearly_ratios = pd.DataFrame()
        yearly_ratios["ROE"] = yearly_income["NetIncome"] / yearly_balance["TotalEquity"]
        yearly_ratios["DebtToEquity"] = yearly_balance["TotalLiabilities"] / yearly_balance["TotalEquity"]
        yearly_ratios["NetMargin"] = yearly_income["NetIncome"] / yearly_income["Revenue"]

        # Có thể làm tương tự cho quarterly nếu cần
        return yearly_ratios

    try:
        yearly_ratios = get_financial_ratios(stock)
        st.header("Chỉ số tài chính hàng năm")
        st.dataframe(yearly_ratios)
    except Exception as e:
        st.error(f"Lỗi khi tải dữ liệu: {e}")

# ==================================================================
# TAB 4 - Báo cáo tài chính
# ==================================================================

def tab4(ticker):
    st.title("Báo cáo tài chính")
    if ticker == '-':
        st.info("Vui lòng chọn mã cổ phiếu.")
        return

    c1, c2 = st.columns(2)
    with c1:
        statement = st.selectbox("Loại báo cáo", ["Income Statement", "Balance Sheet", "Cash Flow"])
    with c2:
        period = st.selectbox("Kỳ báo cáo", ["Yearly", "Quarterly"])

    report_map = {"Income Statement": "income", "Balance Sheet": "balance", "Cash Flow": "cash"}
    period_map = {"Yearly": "year", "Quarterly": "quarter"}

    stock = get_stock_obj(ticker)

    @st.cache_data
    def get_financials(_stock, rtype, ptype):
        if rtype == "income":
            return _stock.finance.income_statement(period=ptype, size=5)
        elif rtype == "balance":
            return _stock.finance.balance_sheet(period=ptype, size=5)
        elif rtype == "cash":
            return _stock.finance.cash_flow(period=ptype, size=5)
        else:
            return None

    df = get_financials(stock, report_map[statement], period_map[period])
    st.dataframe(df)

# ==================================================================
# TAB 5 - Thông tin công ty
# ==================================================================

def tab5(ticker):
    st.title("Thông tin công ty")
    if ticker == '-':
        st.info("Vui lòng chọn mã cổ phiếu.")
        return

    stock = get_stock_obj(ticker)
    if not stock:
        return

    @st.cache_data
    def get_company_overview(_stock):
        return _stock.company.overview()  # sử dụng đúng API

    try:
        df = get_company_overview(stock)
        st.dataframe(df.T)
    except Exception as e:
        st.error(f"Lỗi khi tải thông tin công ty: {e}")
# ==================================================================
# TAB 6 - Monte Carlo Simulation
# ==================================================================

def tab6(ticker):
    st.title("Mô phỏng Monte Carlo")
    if ticker == '-':
        st.info("Vui lòng chọn mã cổ phiếu.")
        return

    simulations = st.selectbox("Số lần mô phỏng", [200, 500, 1000])
    horizon = st.selectbox("Số ngày dự đoán", [30, 60, 90])

    @st.cache_data
    def run_mc(ticker, horizon, sims):
        stock = get_stock_obj(ticker)
        df = stock.history(start=(datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d"),
                           end=datetime.now().strftime("%Y-%m-%d"))
        prices = df["close"]
        daily_ret = prices.pct_change().dropna()
        vol = np.std(daily_ret)
        last_price = prices.iloc[-1]
        sim_df = pd.DataFrame()
        for i in range(sims):
            next_prices = [last_price]
            for _ in range(horizon):
                next_prices.append(next_prices[-1] * (1 + np.random.normal(0, vol)))
            sim_df[i] = next_prices[1:]
        return sim_df, last_price

    sim_df, last_price = run_mc(ticker, horizon, simulations)

    if sim_df.empty:
        st.warning("Không có dữ liệu mô phỏng.")
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(sim_df)
    plt.axhline(y=last_price, color="red")
    st.pyplot(fig)

    st.subheader("Value at Risk (VaR)")
    end_prices = sim_df.iloc[-1]
    percentile_5 = np.percentile(end_prices, 5)
    VaR = last_price - percentile_5
    st.write(f"VaR 95% = {VaR:.2f} VND")

# ==================================================================
# TAB 7 - Xu hướng danh mục
# ==================================================================

vn30_tickers = [
    'ACB', 'BCM', 'BID', 'BVH', 'CTG', 'FPT', 'GAS', 'GVR', 'HDB', 'HPG',
    'MBB', 'MSN', 'MWG', 'PLX', 'POW', 'SAB', 'SSB', 'SSI', 'STB', 'TCB',
    'TPB', 'VCB', 'VHM', 'VIB', 'VIC', 'VJC', 'VNM', 'VPB', 'VRE', 'SHB'
]

def tab7():
    st.title("Xu hướng danh mục của bạn")
    selected = st.multiselect("Chọn các mã", vn30_tickers, default=['FPT', 'VCB', 'HPG'])

    @st.cache_data
    def get_portfolio(tickers):
        data = pd.DataFrame()
        for t in tickers:
            try:
                stock = get_stock_obj(t)
                df = stock.history(start="2020-01-01", end=datetime.today().strftime("%Y-%m-%d"))
                df["Date"] = pd.to_datetime(df["time"])
                df = df.set_index("Date")
                data[t] = df["close"]
            except Exception:
                st.warning(f"Lỗi khi tải {t}")
        return data

    df = get_portfolio(selected)
    if df.empty:
        st.warning("Không có dữ liệu.")
        return

    norm = (df / df.iloc[0] * 100).reset_index().melt("Date", var_name="Ticker", value_name="Normalized")
    fig = px.line(norm, x="Date", y="Normalized", color="Ticker", title="So sánh tăng trưởng danh mục")
    st.plotly_chart(fig, use_container_width=True)

# ==================================================================
# MAIN
# ==================================================================

def run():
    st.sidebar.title("VN30 Dashboard")
    ticker = st.sidebar.selectbox("Chọn mã VN30", ["-"] + vn30_tickers)
    tab = st.sidebar.radio("Chọn tab", ["Tổng quan", "Biểu đồ kỹ thuật", "Chỉ số tài chính",
                                        "Báo cáo tài chính", "Thông tin công ty",
                                        "Mô phỏng Monte Carlo", "Xu hướng danh mục"])

    if tab == "Tổng quan": tab1(ticker)
    elif tab == "Biểu đồ kỹ thuật": tab2(ticker)
    elif tab == "Chỉ số tài chính": tab3(ticker)
    elif tab == "Báo cáo tài chính": tab4(ticker)
    elif tab == "Thông tin công ty": tab5(ticker)
    elif tab == "Mô phỏng Monte Carlo": tab6(ticker)
    elif tab == "Xu hướng danh mục": tab7()


if __name__ == "__main__":
    st.set_page_config(layout="wide")
    run()
