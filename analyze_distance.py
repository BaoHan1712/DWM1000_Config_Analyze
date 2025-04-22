import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
import numpy as np
from scipy.signal import find_peaks
from scipy import stats
import seaborn as sns
from matplotlib.font_manager import FontProperties

def set_plot_style():
    """Thiết lập style cho đồ thị"""
    # Thiết lập style cơ bản
    plt.style.use('default')
    sns.set_style("whitegrid")
    
    # Cấu hình font
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['figure.figsize'] = (20, 25)
    plt.rcParams['figure.dpi'] = 100
    
def detect_anomalies(data):
    """Phát hiện các điểm bất thường bằng nhiều phương pháp"""
    # Z-score
    z_scores = np.abs(stats.zscore(data))
    z_score_anomalies = np.where(z_scores > 3)[0]
    
    # IQR
    Q1 = np.percentile(data, 25)
    Q3 = np.percentile(data, 75)
    IQR = Q3 - Q1
    iqr_anomalies = np.where((data < (Q1 - 1.5 * IQR)) | (data > (Q3 + 1.5 * IQR)))[0]
    
    # Độ biến thiên
    rolling_std = pd.Series(data).rolling(window=5).std()
    variation_anomalies = np.where(rolling_std > rolling_std.mean() + 2 * rolling_std.std())[0]
    
    return z_score_anomalies, iqr_anomalies, variation_anomalies

def analyze_trend(data):
    """Phân tích xu hướng của dữ liệu"""
    x = np.arange(len(data))
    slope, _, _, _, _ = stats.linregress(x, data)
    
    if slope > 0.1:
        return "tang manh"
    elif slope > 0:
        return "tang dan"
    elif slope < -0.1:
        return "giam manh"
    elif slope < 0:
        return "giam dan"
    else:
        return "on dinh"

def analyze_distance_data(excel_file):
    """Phân tích dữ liệu khoảng cách từ file Excel"""
    print("📊 Dang doc du lieu...")
    df = pd.read_excel(excel_file)
    df['Thoi gian'] = pd.to_datetime(df['Thời gian'])
    distances = df['Khoảng cách (mm)'].values
    
    # Tạo thư mục kết quả
    analysis_dir = 'analysis_results'
    if not os.path.exists(analysis_dir):
        os.makedirs(analysis_dir)
    
    # Thiết lập style
    set_plot_style()
    
    try:
        # Tạo figure với 6 subplot
        fig = plt.figure()
        
        # 1. Biểu đồ dữ liệu theo thời gian
        ax1 = plt.subplot(3, 2, 1)
        ax1.plot(df['Thoi gian'], distances, 'b-', linewidth=1, alpha=0.7)
        ax1.set_title('Du lieu theo thoi gian')
        ax1.set_xlabel('Thoi gian')
        ax1.set_ylabel('Khoang cach (mm)')
        ax1.grid(True)
        plt.xticks(rotation=45)
        
        # 2. Biểu đồ phân phối
        ax2 = plt.subplot(3, 2, 2)
        sns.histplot(data=distances, kde=True, ax=ax2)
        ax2.set_title('Phan phoi khoang cach')
        ax2.set_xlabel('Khoang cach (mm)')
        ax2.set_ylabel('Tan suat')
        
        # 3. Box plot
        ax3 = plt.subplot(3, 2, 3)
        sns.boxplot(y=distances, ax=ax3)
        ax3.set_title('Box plot khoang cach')
        ax3.set_ylabel('Khoang cach (mm)')
        
        # 4. Biểu đồ điểm bất thường
        z_anom, iqr_anom, var_anom = detect_anomalies(distances)
        ax4 = plt.subplot(3, 2, 4)
        ax4.plot(df['Thoi gian'], distances, 'b-', label='Du lieu', alpha=0.5)
        ax4.scatter(df['Thoi gian'].iloc[z_anom], distances[z_anom], 
                   color='red', label='Z-score', alpha=0.5)
        ax4.scatter(df['Thoi gian'].iloc[iqr_anom], distances[iqr_anom], 
                   color='green', label='IQR', alpha=0.5)
        ax4.scatter(df['Thoi gian'].iloc[var_anom], distances[var_anom], 
                   color='orange', label='Bien thien', alpha=0.5)
        ax4.set_title('Phat hien diem bat thuong')
        ax4.set_xlabel('Thoi gian')
        ax4.set_ylabel('Khoang cach (mm)')
        ax4.legend()
        plt.xticks(rotation=45)
        
        # 5. Biểu đồ xu hướng
        ax5 = plt.subplot(3, 2, 5)
        x = np.arange(len(distances))
        z = np.polyfit(x, distances, 1)
        p = np.poly1d(z)
        ax5.plot(df['Thoi gian'], distances, 'b.', alpha=0.5, label='Du lieu')
        ax5.plot(df['Thoi gian'], p(x), 'r-', label='Xu huong')
        ax5.set_title('Phan tich xu huong')
        ax5.set_xlabel('Thoi gian')
        ax5.set_ylabel('Khoang cach (mm)')
        ax5.legend()
        plt.xticks(rotation=45)
        
        # 6. Báo cáo thống kê
        ax6 = plt.subplot(3, 2, 6)
        ax6.axis('off')
        
        # Tính toán các chỉ số thống kê
        all_anomalies = np.unique(np.concatenate([z_anom, iqr_anom, var_anom]))
        stats_text = f"""THONG KE CO BAN
------------------------
So luong mau: {len(distances)}
Gia tri nho nhat: {np.min(distances):.2f}
Gia tri lon nhat: {np.max(distances):.2f}
Gia tri trung binh: {np.mean(distances):.2f}
Do lech chuan: {np.std(distances):.2f}
Trung vi: {np.median(distances):.2f}

PHAN TICH BAT THUONG
------------------------
Tong so diem bat thuong: {len(all_anomalies)}
Ty le bat thuong: {(len(all_anomalies)/len(distances))*100:.2f}%

Chi tiet cac loai:
- Theo Z-score: {len(z_anom)}
- Theo IQR: {len(iqr_anom)}
- Theo do bien thien: {len(var_anom)}

XU HUONG
------------------------
He so goc: {z[0]:.4f}
Xu huong chung: {analyze_trend(distances)}"""
        
        ax6.text(0, 1, stats_text, fontsize=10, 
                verticalalignment='top', horizontalalignment='left',
                transform=ax6.transAxes, family='monospace')
        
        plt.tight_layout(pad=3.0)
        
        # Lưu kết quả
        result_path = f"{analysis_dir}/analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(result_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Da luu ket qua phan tich vao: {result_path}")
        
    except Exception as e:
        print(f"Loi khi phan tich du lieu: {str(e)}")
        plt.close()

if __name__ == "__main__":
    log_dir = 'logs'
    if os.path.exists(log_dir):
        excel_files = [f for f in os.listdir(log_dir) if f.endswith('.xlsx')]
        if excel_files:
            excel_paths = [os.path.join(log_dir, f) for f in excel_files]
            latest_file = max(excel_paths, key=os.path.getmtime)
            analyze_distance_data(latest_file)
        else:
            print("X Khong tim thay file Excel trong thu muc logs")
    else:
        print("X Khong tim thay thu muc logs") 