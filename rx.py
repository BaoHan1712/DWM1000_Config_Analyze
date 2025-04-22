import serial
import threading
import queue
import time
from cover.utils import *


# Queue để chia sẻ dữ liệu giữa 2 luồng
distance_queue = queue.Queue()

# Khởi tạo cổng Serial
ser_esp32 = serial.Serial('COM4', 115200, timeout=1) 

# Định nghĩa các byte đặc biệt
START_BYTE = 0x02
END_BYTE = 0x03

def receive_thread():
    """Luồng nhận dữ liệu từ ESP32 (UWB DW1000)"""
    print("⏳ Đang khởi động và chờ hệ thống ổn định...")
    
    # Thời gian chờ khởi động và ổn định (3 giây)
    time.sleep(3)
    
    # Xóa buffer cũ tích tụ trong thời gian chờ
    if ser_esp32.in_waiting:
        ser_esp32.reset_input_buffer()
    
    print("✅ Bắt đầu nhận dữ liệu từ ESP32 UWB...\n")
    
    # Đếm số lần đọc thành công để đảm bảo ổn định
    stable_count = 0
    is_stable = False
    
    while True:
        try:
            if ser_esp32.in_waiting:
                byte = ser_esp32.read()
                
                if byte[0] == 0x02:  # Tìm thấy byte bắt đầu
                    data = ser_esp32.read(3)
                    if len(data) == 3 and data[2] == 0x03:  # Kiểm tra byte kết thúc
                        distance = (data[0] << 8) | data[1]
                        
                        if not is_stable:
                            stable_count += 1
                            if stable_count >= 10:  # Đợi 10 lần đọc thành công
                                is_stable = True
                                print("✅ Hệ thống đã ổn định, bắt đầu truyền dữ liệu...")
                        
                        if is_stable:
                            try:
                                # Xóa hết queue cũ để lấy dữ liệu mới nhất
                                while not distance_queue.empty():
                                    distance_queue.get_nowait()
                                distance_queue.put_nowait(distance)
                                print(f"✅ Khoảng cách UWB: {distance} mm")
                            except:
                                pass

            time.sleep(0.0001)

        except serial.SerialException as e:
            print(f"❌ Lỗi kết nối Serial ESP32: {e}")
            # Reset các biến trạng thái
            stable_count = 0
            is_stable = False
            time.sleep(0.1)
            try:
                ser_esp32.close()
                ser_esp32.open()
                ser_esp32.reset_input_buffer()
            except:
                pass
            
        except Exception as e:
            print(f"❌ Lỗi không xác định: {e}")
            stable_count = 0
            is_stable = False
            time.sleep(0.01)

def main():
    # Khởi tạo và chạy thread nhận dữ liệu
    rx_thread = threading.Thread(target=receive_thread, daemon=True)
    rx_thread.start()

    # Vòng lặp chính để xử lý dữ liệu từ queue
    try:
        while True:
            try:
                distance = distance_queue.get()
                # Xử lý thêm dữ liệu khoảng cách ở đây nếu cần
            except queue.Empty:
                continue
    except KeyboardInterrupt:
        print("\n🛑 Đang dừng chương trình...")
    finally:
        ser_esp32.close()

if __name__ == "__main__":
    main()