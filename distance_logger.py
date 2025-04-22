import serial
import pandas as pd
from datetime import datetime
import time
import os

# Khởi tạo Serial connection
ser_esp32 = serial.Serial('COM7', 115200, timeout=1)  

def create_excel_file():
    """Tạo file Excel mới với tên theo thời gian"""
    now = datetime.now()
    filename = f"distance_log_{now.strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    # Tạo DataFrame với các cột cần thiết
    df = pd.DataFrame(columns=['Thời gian', 'Khoảng cách (mm)'])
    
    # Tạo thư mục logs nếu chưa tồn tại
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Lưu file Excel
    filepath = os.path.join('logs', filename)
    df.to_excel(filepath, index=False)
    return filepath, df

def log_distance():
    """Đọc và ghi dữ liệu khoảng cách vào Excel"""
    print("⏳ Đang khởi động và tạo file Excel...")
    
    filepath, df = create_excel_file()
    print(f"✅ Đã tạo file: {filepath}")
    
    # Khởi tạo biến đếm để định kỳ lưu file
    save_counter = 0
    SAVE_INTERVAL = 10  # Lưu sau mỗi 10 lần ghi
    
    print("⏳ Bắt đầu ghi dữ liệu...")
    
    try:
        while True:
            if ser_esp32.in_waiting:
                byte = ser_esp32.read()
                
                if byte[0] == 0x02:  # Start byte
                    data = ser_esp32.read(3)
                    if len(data) == 3 and data[2] == 0x03:  # End byte
                        # Tính khoảng cách
                        distance = (data[0] << 8) | data[1]
                        
                        # Lấy thời gian hiện tại
                        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                        
                        # Thêm dữ liệu vào DataFrame
                        new_row = pd.DataFrame({
                            'Thời gian': [current_time],
                            'Khoảng cách (mm)': [distance]
                        })
                        df = pd.concat([df, new_row], ignore_index=True)
                        
                        # In ra màn hình
                        print(f"📝 {current_time} - Khoảng cách: {distance} mm")
                        
                        # Tăng biến đếm và lưu file định kỳ
                        save_counter += 1
                        if save_counter >= SAVE_INTERVAL:
                            df.to_excel(filepath, index=False)
                            print(f"💾 Đã lưu dữ liệu vào {filepath}")
                            save_counter = 0
                            
            time.sleep(0.001)  # Giảm tải CPU
            
    except KeyboardInterrupt:
        print("\n🛑 Đang dừng ghi dữ liệu...")
    except Exception as e:
        print(f"❌ Lỗi: {e}")
    finally:
        # Lưu lần cuối trước khi thoát
        df.to_excel(filepath, index=False)
        print(f"💾 Đã lưu dữ liệu cuối cùng vào {filepath}")
        ser_esp32.close()
        print("📍 Đã đóng cổng Serial")

if __name__ == "__main__":
    log_distance() 