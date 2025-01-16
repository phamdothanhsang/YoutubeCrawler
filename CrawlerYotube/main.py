from function import * # Tại đây import các thư viện và hàm hỗ trợ từ file function

# Khởi tạo hàm để bắt đầu chạy chương trình

def main():
    
    while 1:

        with open("listUserNeedCrawVideo.txt", "r", encoding="utf-8") as file:

            for lineInforCheck in file:  # Tại đây phân tích lấy thông tin từng dòng của file " listUserNeedCrawVideo.txt "
                
                remove_Data_For_New_Loop()
                
                # Kiểm tra nếu string không có dấu /+/ thì bỏ qua
                if check_slash_plus(lineInforCheck) == False: continue
                
                string = lineInforCheck.strip()

                values = string.split("/+/")  # Tách chuỗi để phân tích lấy IDVideo theo ChanelConfigID

                # Lấy thông tin ChannelConfigID + Tên Kênh để tải video
                print("Craw Video from User:",remove_Space_In_Text(str(values[1])))

                functionSendMessageToTelegram("Bắt đầu kiểm tra craw Video của User: " + remove_Space_In_Text(str(values[1])))
                print("idtest:",remove_Space_In_Text)
                # Hàm runCrawlerVideoTiktok sẽ chạy theo thứ tự các ChannelConfigID trong list để tải video về
                idUser_get = remove_Space_In_Text(values[1])

                channelConfigID_get  = remove_Space_In_Text(values[0])

                crawlMethod_get = remove_Space_In_Text(values[2])

                default_ribbon_get = remove_Space_In_Text(values[4])

                default_keyword_get = remove_Space_In_Text(values[5])

                runProgram(idUser_get,channelConfigID_get,crawlMethod_get,default_ribbon_get,default_keyword_get)
                
        functionSendMessageToTelegram("Đã chạy xong 1 vòng lặp => Bắt đầu vòng lặp mới")
        
main()