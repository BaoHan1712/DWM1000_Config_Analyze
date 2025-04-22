import serial
import re
import threading
import queue
import time
from cover.utils import *


# Queue để chia sẻ dữ liệu giữa 2 luồng
distance_queue = queue.Queue()

# Khởi tạo 2 cổng Serial
ser_esp32 = serial.Serial('COM7', 115200, timeout=1)  # Cổng nhận từ ESP32
ser_stm32 = serial.Serial('COM4', 115200)  # Cổng gửi xuống STM32

def receive_thread():
    """Luồng nhận dữ liệu từ ESP32 (UWB DW1000)"""
    print("⏳ Đang khởi động và chờ hệ thống ổn định...")
    
    # Thời gian chờ khởi động và ổn định (3 giây)
    time.sleep(5)
    
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
                                # print(f"✅ Khoảng cách UWB: {distance} mm")
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

def transmit_thread():
    """Luồng gửi dữ liệu xuống STM32"""
    print("⏳ Bắt đầu gửi dữ liệu xuống STM32...\n")
    last_sent = 0
    last_sent_time = time.time()
    
    while True:
        try:
            current_time = time.time()
            
            # Xóa buffer cũ của STM32 nếu có
            if ser_stm32.in_waiting:
                ser_stm32.reset_input_buffer()
                
            # Xóa buffer gửi nếu có
            if ser_stm32.out_waiting:
                ser_stm32.reset_output_buffer()

            # Lấy distance từ queue với timeout ngắn
            try:
                distance = distance_queue.get(timeout=0.1)  

                # Chỉ gửi nếu khác giá trị cũ và đã đủ thời gian
                if distance != last_sent and (current_time - last_sent_time) > 0.05:  # 50ms delay
                    try:
                        create_stm32_message_1(1, distance, ser_stm32)
                        print(f"📤 Đã gửi xuống STM32: {distance} mm")
                        last_sent = distance
                        last_sent_time = current_time
                        
                        # Đảm bảo dữ liệu được gửi đi
                        ser_stm32.flush()
                        
                    except serial.SerialException:
                        print("❌ Lỗi kết nối STM32, đang thử kết nối lại...")
                        time.sleep(0.5)
                        try:
                            ser_stm32.close()
                            ser_stm32.open()
                        except:
                            pass
                
            except queue.Empty:
                # Timeout khi đợi dữ liệu mới
                continue
            
            # Thêm small delay để tránh CPU quá tải
            time.sleep(0.001)
            
        except Exception as e:
            print(f"❌ Lỗi ở luồng gửi: {e}")
            time.sleep(0.1)


def main():
    print("🚀 Khởi động chương trình...")
    print(f"COM ESP32: {ser_esp32.port}, COM STM32: {ser_stm32.port}")
    
    # Tạo và khởi động các luồng
    receiver = threading.Thread(target=receive_thread)
    transmitter = threading.Thread(target=transmit_thread)
    
    # Đặt các luồng là daemon
    receiver.daemon = True
    transmitter.daemon = True
    
    # Khởi động các luồng
    receiver.start()
    transmitter.start()
    
    try:
        # Giữ chương trình chạy
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Đang dừng chương trình...")
    finally:
        # Đóng các cổng Serial
        ser_esp32.close()
        ser_stm32.close()
        print("📍 Đã đóng các cổng Serial")

if __name__ == "__main__":
    main()