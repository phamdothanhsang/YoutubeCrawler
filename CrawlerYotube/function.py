import pyautogui
import pyperclip
import win32api
import win32con
import time
import random
import shutil
import webbrowser as wb
import re
from urllib import request
from bs4 import BeautifulSoup
import requests
import os
import subprocess
import psycopg2
from datetime import datetime
from PIL import ImageGrab
import glob
from transcode_api import *
import cv2
from pytube import YouTube
from pytube.exceptions import PytubeError
import yt_dlp 


os.environ['NODE_TLS_REJECT_UNAUTHORIZED'] = '0'
 
# Tại đây khởi tạo các giá trị hỗ trợ chạy xuyên suốt chương trình

urlChrome = "C:/Program Files/CocCoc/Browser/Application/browser.exe %s" # Trinh` duyet open link video

imgUrl = "img/"

confidenceImg = 0.8

videoID_In_DB_After_Upload = []

# Khung hình tương tác
areaDisplayPC = [1920, 1080]
#areaDisplayPC = [1024, 768]S

def download_video(link):
    try:
        yt = YouTube(link)
        print("Tiêu đề:", yt.title)
    except KeyError:
        print("Không thể truy cập videoDetails. Có thể YouTube đã thay đổi API.")
    except PytubeError as e:
        print(f"Lỗi Pytube: {e}")
    except Exception as e:
        print(f"Lỗi không xác định: {e}")

# Hàm upload size cho Video sau khi tải về 
def update_Width_Height_Video():
    
    value_Break_While = [0]
    
    # Các bước sẽ thực hiện 
        # Bước 1: Lấy ID video theo vòng lặp từ lớn đến nhỏ, có khung Weight trống
        # Bước 2: Lưu đè giá trị vào file txt
        # Bước 3: Tiến hành vòng lặp để lấy VideoScreenShot có trong DB, để xác định kích thước
    
    # --------------------------------------- /

    # Hàm lấy width, height của video
    def get_video_dimensions(video_url):
        
        try:
            cap = cv2.VideoCapture(video_url)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            return width, height

        except Exception as e: print("Error:", e)
        
        return None, None

    # Hàm lấy các ID video từ DB
    def get_Information_VideoID_New():
        
        Data_Save = [[],[],[]]
        cur = connectDB().cursor()

        # Hàm hỗ trợ lấy dữ liệu ChannelConfigID + ID video tiktok + thời gian tải lên
        
        cur.execute( 'SELECT "VideoID", "RawPlayURL" FROM "Videos" WHERE "Height" IS NULL ORDER BY "VideoID" DESC LIMIT 5' )

        rows = cur.fetchall()

        # Lưu vào Data => Chuẩn bị tới bước tiếp theo phân loại và xóa trash
        for row in rows: 
            
            Data_Save[0].append(row[0])
            
            # Lấy width, height của video
            height, width = get_video_dimensions(row[1])
            Data_Save[1].append(height)
            Data_Save[2].append(width)

        # Ngắt kết nối khi lấy dữ liệu xong

        cur.close()
        connectDB().close()
        
        return Data_Save

    
    # Hàm update lại Code random cho DB Photos
    def Update_Code_Random_DB(Height ,Width, VideoID):
        
        if int(Height) > int(Width): IsVertical = True
        else: IsVertical = False
        Width = int(Width)
        Height = int(Height)
        VideoID = int(VideoID)
        # Tạo kết nối đến cơ sở dữ liệu
        connection = connectDB()
        cur = connection.cursor()

        # Thực hiện lệnh SQL để cập nhật cột "Code"
    
        cur.execute('UPDATE "Videos" SET "Height" = %s, "Width" = %s , "IsVertical" = %s Where "VideoID" = %s ', (int(Height), int(Width), IsVertical, VideoID))


        # Commit thay đổi vào cơ sở dữ liệu và đóng kết nối
        connection.commit()
        cur.close()
        connection.close()
    
    # Chạy test
    data_Update_DB = get_Information_VideoID_New()

    if len(data_Update_DB[0]) > 0:
        
        Update_Code_Random_DB(data_Update_DB[2][0], data_Update_DB[1][0], data_Update_DB[0][0])
        print('/-- Update for VideoID: ', data_Update_DB[0][0], ' --/')
    
    # Thêm điều kiện để break While
    else: 
        print("Không còn VideoID nào cần update")
        value_Break_While.insert(0,1)

# Hàm kết nối tới DB
def connectDB():

        conn = psycopg2.connect(
            host="172.16.33.100",
            port="5432",
            database="WAN_Data",
            user="wan_data",
            password="fbpSk9MPmjheVzEtR8Ax6Q4NWYa3JnqG"
        )

        return(conn)

# Hàm kiểm tra có file video Mp4 nào trong Foldẻ hay không
def check_File_Video_Mp4(folder_Path_Input):

    # Kiểm tra xem đường dẫn thư mục có tồn tại không
    if os.path.exists(folder_Path_Input):
        # Lấy danh sách tệp trong thư mục
        file_list = os.listdir(folder_Path_Input)
        
        # Lọc ra các tên tệp có phần mở rộng .mp4
        mp4_files = [file for file in file_list if file.endswith(".mp4")]
        
        # In danh sách tên các tệp .mp4
        for mp4_file in mp4_files:
            return(mp4_file)
            
# Hàm hỗ trợ kiểm tra trạng thái download ...
def check_Status_Download_Video(File_Path_Input):
    
    print("Download ... ")
    
        # Tại đây thực hiện vòng lặp check thời gian tải Video xuống
    while 1:
        # Nếu tải thành công 
        if os.path.exists(File_Path_Input):
            print("Download done")
            time.sleep(5) 
            return True
            
# Hàm hỗ trợ tải Video xuống như bấm vào Download nhưng nhanh hơn nhiều
# def tool_Help_Run_Download_Video(video_Url_Input):
    
#     try:
#         # Đường dẫn đến video YouTube bạn muốn tải
#         video_Url_Input = str(video_Url_Input)

#         # Tạo đối tượng YouTube
#         yt = YouTube(video_Url_Input)

#         # Kiểm tra nếu không thể truy cập tiêu đề
#         if 'videoDetails' not in yt.vid_info:
#             print("Không thể truy cập videoDetails. Có thể YouTube đã thay đổi API.")
#             return False

#         # Lấy thông tin về video
#         print("Tiêu đề:", yt.title)
#         print("Thời lượng (giây):", yt.length)

#     # Chọn định dạng và chất lượng tải xuống
#     # Chọn định dạng và chất lượng tải xuống
#     # Ví dụ: chọn định dạng mp4 và chất lượng cao nhất
#         # Chọn định dạng và chất lượng tải xuống
#     # Ví dụ: chọn định dạng mp4 và chất lượng cao nhất
#         video_stream = yt.streams.get_highest_resolution()

#         # Tải video xuống
#         output_path = 'uploadConvertVideo'
#         video_stream.download(output_path=output_path)
            
#         print("\nVideo đã được tải xuống và lưu tại:", output_path)
    
#         return True

#     except PytubeError as e:
#         print(f"Lỗi Pytube: {e}")
#         return False
#     except Exception as e:
#         print(f"Lỗi không xác định: {e}")
#         return False


def tool_Help_Run_Download_Video(video_Url_Input):
    try:
        output_path = 'uploadConvertVideo'
        ydl_opts = {
            'format': 'best',  # Chọn định dạng tốt nhất
            'outtmpl': f'{output_path}/%(title)s.%(ext)s',  # Định dạng tên file
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_Url_Input])

        print("Video đã được tải xuống thành công.")
        return True
    except Exception as e:
        print(f"Lỗi khi tải video: {e}")
        return False
# Hàm hiển thị % khi đang tải Video
def on_Progress_Download_Video(stream, chunk, remaining):
    # Tính phần trăm hoàn thành tải
    percent = (1 - remaining / stream.filesize) * 100
    print(f"{percent:.1f}% đã tải xong", end='\r')

# Hàm đổi tên Video, sau khi download xong
def change_Title_Video_After_Download(file_Name_Input, title_Video_Change_Input, folder_Path_Input):
    
    # Sau đó sẽ đổi tên file thành tên khác
    old_File_Name = file_Name_Input
    new_File_Name = title_Video_Change_Input + '.mp4'

    old_File_Path = os.path.join(folder_Path_Input, old_File_Name)
    new_file_path = os.path.join(folder_Path_Input, new_File_Name)

    if os.path.exists(old_File_Path):
        
        os.rename(old_File_Path, new_file_path)
        print("Change the name ... Done")
        time.sleep(2)
        # Tiến hành tải Hình bìa Video
        get_Thummnail_Video(title_Video_Change_Input)
    
    time.sleep(2)
        
# Kiểm tra đường truyển mạng ...
def checkHaveFileDownload_or_Not(folder_path):
    
    folder_path = "uploadConvertVideo"

    for i in range(60):
        print("Bắt đầu kiểm tra quá trình download ... ", i)

        time.sleep(1)
        
        if i == 55: 
            
            print("Kết nối mạng bị lỗi ... Không tiếp tục tải được Video")
            functionSendMessageToTelegram("Kết nối mạng bị lỗi ... Không tiếp tục tải được Video")
            return False
        
        # Kiểm tra kết nối mạng khi đang download có đang bình thường hay không hay file bị lỗi
        if check_Qty_File_Have_When_Download(folder_path) > 1:
            
            print("Kết nối mạng bình thường ... Bắt đầu download")
            time.sleep(1)
            return True
            
# Kiểm tra số lượng file trong thư mục
def check_Qty_File_Have_When_Download(folder_path_Input):

    folder_Count = os.listdir(folder_path_Input)

    # Sử dụng len để đếm số lượng tệp tin
    return len(folder_Count)
    
# Hàm chính triển khai download Video
def download_Video_Step_2(channel_ConfigID_Input_4, ID_User_4,
                            default_Ribbon_4, default_Keyword_5,
                            data_IDVideo_Title_Hashtag_Input):
    
    if len(data_IDVideo_Title_Hashtag_Input[0]) > 0: 
    
        # Hàm chạy tải từng link Video đã lấy
        for i in range(len(data_IDVideo_Title_Hashtag_Input[1])):
            
            # Tại bước này Crawler Video Về trước ( Video đúng chuẩn + không có Logo )
            print("ID Video: ",data_IDVideo_Title_Hashtag_Input[0][i]," || Title Video: ",data_IDVideo_Title_Hashtag_Input[1][i])
            
            # Hàm kiểm tra xem video này đã có chưa
            if Check_ID_Video_Have_Download_Or_Not(channel_ConfigID_Input_4, data_IDVideo_Title_Hashtag_Input[0][i] ) == False:
                print("Video này đã có ... check Video khác ...")
                continue
            
             # Hàm giúp xóa các thông tin để bắt đầu vòng lặp mới
            remove_Data_For_New_Loop()

            print("Start Download This Video =>")
            functionSendMessageToTelegram("Tải Video: https://www.youtube.com/watch?v=" + data_IDVideo_Title_Hashtag_Input[0][i])

            # Step 1: Download Video ...
            download_Video_Step_1(
                "https://www.youtube.com/watch?v=" + data_IDVideo_Title_Hashtag_Input[0][i] ,
                str(data_IDVideo_Title_Hashtag_Input[0][i]).replace("/+/", ""),
                str(data_IDVideo_Title_Hashtag_Input[1][i]).replace("/+/", ""),
                str(data_IDVideo_Title_Hashtag_Input[2][i]).replace("/+/", ""), str(ID_User_4),
                channel_ConfigID_Input_4, default_Ribbon_4, default_Keyword_5)

    else:
            print("Kênh đã được thay đổi ID User => Không tìm thấy Video nào cả !")
            functionSendMessageToTelegram("Kênh đã được thay đổi ID User => Không tìm thấy Video nào cả !")
                
# Hàm kiểm tra file video đang download, có lỗi hay không 
def check_Video_Dowloading_Have_Error_or_Not(Id_Video_Input):
    
    Id_Video_Input = str(Id_Video_Input)
    Id_Video_Input = Id_Video_Input.strip()

    if checkHaveFileDownload_or_Not('uploadConvertVideo', Id_Video_Input) == False: return False 

    print("Downloading ...")
    functionSendMessageToTelegram("Downloading ...")

    # Tại đây sẽ kiểm tra Video downloading ...
    check_File_Video_Download_To_Finish(Id_Video_Input)
        
# Hàm phân tích lấy thông tin ID Video + Title, ... cho page có Playlist
def get_ID_Video_PlayList_Page(source_Code_Input):
    
    data_Save = [[],[],[]]
    bodyGet = []
    
    # Source get
    htmlSoure = BeautifulSoup(source_Code_Input, 'html.parser')


    # Lấy tất cả các thẻ <div> có id="contents" và class="style-scope ytd-playlist-video-list-renderer style-scope ytd-playlist-video-list-renderer"
    contents_elements = htmlSoure.find_all('div', {'id': 'contents', 'class': 'style-scope ytd-rich-grid-renderer'})
    # Kiểm tra nếu có các phần tử thoả mãn điều kiện
    if contents_elements:
        for content_element in contents_elements:
            all_html = content_element.prettify()
            bodyGet.insert(0,all_html)
    
    # Sử dụng Body Source này để lấy ID + Title Video
    bodyGet_use = str(bodyGet[0])
        
    # Bước 3 => Lấy ID video 
    soup = BeautifulSoup(bodyGet_use, 'html.parser')
    links = soup.find_all('a', class_='yt-simple-endpoint inline-block style-scope ytd-thumbnail')
    
    for link in links:
        data_Save[0].append(link['href'].replace("/watch?v=", ""))
        
    # Bước 4 => Lấy Title của Video
    htmlSoure = BeautifulSoup(bodyGet_use, 'html.parser')
    
    rich_grid_rows_3 =  htmlSoure.find_all('a', {'id': 'video-title'})
    
    for i in range(len(rich_grid_rows_3)):
        
        # Xóa html trong string
        soup = BeautifulSoup(str(rich_grid_rows_3[i]), "html.parser")
        text = soup.get_text()
        text = text.strip()
        
        # Save Title 
        data_Save[1].append(text)  
        data_Save[2].append(text)
    
    # In ra --->
    return(data_Save)
        
# Hàm phân tích lấy thông tin trong SourceCode để lấy ID Video cần tải về
def get_Data_Video_Nomarl_Page(source_Code_Input):
    
    data_Save = [[],[],[]]
    
    bodyGet_1 = []
    
    bodyGet_2 = []
    
    # Source get
    htmlSoure = BeautifulSoup(source_Code_Input, 'html.parser')

    # Bước 1 -> Lọc ra div chứa các ID Video
    rich_grid_rows_1 = htmlSoure.find_all('div', class_='style-scope ytd-two-column-browse-results-renderer')
    for i in rich_grid_rows_1:
        bodyGet_1.append(i)
    
    # Bước 2 -> Lọc ID VideoTheo Hàng
    rich_grid_rows_2 =  bodyGet_1[0].find_all('ytd-rich-item-renderer', class_='style-scope ytd-rich-grid-renderer')
    for i in rich_grid_rows_2: bodyGet_2.append(str(i))
        
    # Sử dụng Body Source này để lấy ID + Title Video
    bodyGet_2_String = ' '.join(bodyGet_2) 
        
    # Bước 3 => Lấy ID video 
    soup = BeautifulSoup(bodyGet_2_String, 'html.parser')
    links = soup.find_all('a', class_='yt-simple-endpoint inline-block style-scope ytd-thumbnail')
    
    for link in links:
        data_Save[0].append(link['href'].replace("/watch?v=", ""))
        
    # Bước 4 => Lấy Title của Video
    htmlSoure = BeautifulSoup(bodyGet_2_String, 'html.parser')
    
    rich_grid_rows_3 =  htmlSoure.find_all('yt-formatted-string', id='video-title')
    
    for i in range(len(rich_grid_rows_3)):
        
        # Xóa html trong string
        soup = BeautifulSoup(str(rich_grid_rows_3[i]), "html.parser")
        text = soup.get_text()
        
        # Save Title 
        data_Save[1].append(text)  
        data_Save[2].append(text) 
    
    # In ra --->
    return(data_Save)
            
# Hàm giúp upload Video lên S3 -> DB
def upload_Video_To_S3_And_To_DB(ID_Video_Input_3, channel_ConfigID_Input_3):
    
    for i in range(3):

        print("Upload lên DB: ," ,i)
        
        if i == 2: return False # Upload không thành công

        try:
            # Chạy file này để upload lên Database Weallnet
            subprocess.run(["cmd.exe", "/c", "runS3Weallnet"])  
            time.sleep(3)

        except : functionSendMessageToTelegram("Video upload lên S3 không thành công !")

        if connectDB_Check_File_When_Upload_To_DB(str(ID_Video_Input_3)) == True:

            print("Upload FILE Video => Thanh Cong")
            functionSendMessageToTelegram("Video upload lên DB thành công !")


            
            return True
        
# Hàm hỗ trợ kiểm tra trạng thái download đã xong chưa, sau đó đổi tên theo tùy chỉnh
def check_File_Video_Download_To_Finish(title_Video_Change):
    
    title_Video_Change = str(title_Video_Change)
    
    name_Video_Found = []
    
    folder_Path = "uploadConvertVideo"

    file_Names = []
    
    # Khởi tạo chạy hàm chính
    time.sleep(5)   
    
    try: 

        if os.path.exists(folder_Path):
            file_Names = [name for name in os.listdir(folder_Path) if name.endswith(".mp4.crdownload")]

        for name in file_Names:
            name_Video_Found.insert(0,name.replace(".crdownload", ""))

        # Kiểm tra khi file đã download xong 
        file_Name = str(name_Video_Found[0])
        file_path = os.path.join(folder_Path, file_Name)

        # Kiểm tra tải thành công hay thất bại -> Để tiếp tục hay bắt đầu vòng lặp mới
        check_Status_Download_Video(file_path)
        
        # Hàm đổi tên Video, sau khi download xong
        change_Title_Video_After_Download(file_Name, title_Video_Change, folder_Path)

        return True
            
    except: 
        
        try:
            # Trường hợp download quá nhanh 
            video_Mp4_Title = check_File_Video_Mp4(folder_Path)
            video_Mp4_Title = video_Mp4_Title.replace("uploadConvertVideo", "")
            
            print("Download quá nhanh ... Done")   
            
            # Hàm đổi tên Video, sau khi download xong
            change_Title_Video_After_Download(video_Mp4_Title, title_Video_Change, folder_Path)
            
            time.sleep(3)
            return True
        except:
            
            print("Don't have any Video have download !")
            return False

# Click vào nút download Video
def click_To_Download_Button():
    
    for i in range(30):

        if i == 29: return False
        
        time.sleep(1)
        
        if functionCheckIconHaveOrNot("iconDownloadVideoStep2.jpg") == True: 
            time.sleep(2)
            mouseCursorPositioning("iconDownloadVideoStep2.jpg","Click to download Video ...", 5,5)
            time.sleep(2)
            closeWebBrowser()
            return True 
        
# Hàm truy cập trang để lấy link tải Video xuống
def click_Begin_Download_Video(link_Video_Input, id_Video_Input):
    
    folder_Path = 'uploadConvertVideo'
    
    # Hàm chạy đi tải Video xuống
    if tool_Help_Run_Download_Video(link_Video_Input) == True:
        
        video_Mp4_Title = check_File_Video_Mp4(folder_Path)
    
        # Tại đây sẽ thêm hàm thay đổi tên + tải hình bìa
        change_Title_Video_After_Download(video_Mp4_Title, id_Video_Input, folder_Path)
        
# Hàm này xử lý công việc sau: Download Video => Get Information => Upload to S3 => Upload to Database
def download_Video_Step_1(link_Video_Input, 
                                ID_Video_Input, 
                                title_Video_Input, 
                                hashtag_Video_Input, 
                                id_USer_Input, 
                                channel_ConfigID_Input,  
                                default_Ribbon_Input,
                                default_Keyword_Input):

    # Click vào nút download Video và chờ đến khi xong -> Chuyển sang bước tiếp theo
    if click_Begin_Download_Video(link_Video_Input, ID_Video_Input) == False: 
        print("Video này không download được, chuyển Video khác ...")
        return False

    # Tại đây xử lý video upload lên Database -> Kiểm tra lần nữa -> upload len S3 
    writeTo_uploadedAndDeletedInfo(channel_ConfigID_Input,
                                    ID_Video_Input, 
                                    title_Video_Input, 
                                    hashtag_Video_Input, 
                                    default_Ribbon_Input, 
                                    default_Keyword_Input) 

    # Tiền hành upload lên S3 -> DB
    if upload_Video_To_S3_And_To_DB(ID_Video_Input, channel_ConfigID_Input) == True: 
        
        # Lưu video đã download vào file listDownloadedVideos -> Thành Công !
        writeTo_listDownloadedVideos(id_USer_Input, channel_ConfigID_Input, ID_Video_Input, title_Video_Input, hashtag_Video_Input)  
        
        # Tại đây sẽ kiểm tra nếu Video đã được transcode xong theo kế hoạch thì tiếp tục tải Video khác
        #run_Soft_Transcode_Video(videoID_In_DB_After_Upload[0])
        
    else: 
        # Lưu video đã download vào file unavailableVideosList -> Không thành công 
        print("Upload FILE Video => Khong Thanh Cong => Save Vao List")
        writeTo_unavailableVideosList(id_USer_Input, channel_ConfigID_Input, ID_Video_Input, title_Video_Input, hashtag_Video_Input) # Save du lieu upload Fail
      
# Hàm kiểm tra ID Video dựa trên ChannelConfigID, xem video muốn tải đã tồn tại hay chưa
def Check_ID_Video_Have_Download_Or_Not(channel_ConfigID_Input, ID_Video_Want_Check):

    valueCheckTrueFalse = []

    resultFinal = [0]

    with open("listDownloadedVideos.txt", "r", encoding="utf-8") as file:

        for lineInforCheck in file:  # Tai day lay ra tung` dong` cua file

            string = lineInforCheck.strip()

            values = string.split("/+/")  # Tách chuỗi để phân tích IDVideo theo ChanelConfigID
            values[0] = values[0].replace('\ufeff', '')

            # So sanh tu` ChannelConfigID
            if str(channel_ConfigID_Input.strip()) == str(values[0].strip()):
                
                # Check xem video nay da~ co' trong list chua => Neu' Co' Khong Download nua~
                valueCheckTrueFalse.append(remove_Space_In_Text(str(values[2])))

    # Kết quả Video lọc ra => kiểm tra
    for i in valueCheckTrueFalse:

        if remove_Space_In_Text(ID_Video_Want_Check) == i:
            # Gán điều kiện không tải video này nữa
            resultFinal.insert(0, 1)
            break

    # Kết quả trả về cuối cùng sau khi kiểm tra
    if resultFinal[0] == 1: return False
    else: return True # Có thể tải video này nếu là True
    
# Hàm kiểm tra ID Video có trong DB hay chưa
def connectDB_Check_File_When_Upload_To_DB(ID_Video_Check_Input): 

    print("Connect Database")

    idVideoGetFromDB = []

    try:
        
        # Tạo cursor để thao tác với database
        cursor = connectDB().cursor()

        # Thực hiện truy vấn SQL để lấy 1 giá trị IDVideo mới nhất
        cursor.execute('SELECT "ReferenceSource", "VideoID" FROM "Videos" WHERE "ReferenceSource" LIKE %s AND "Enable" = true ORDER BY "CreatedDate" DESC LIMIT 1', ('youtube%',))
        rows = cursor.fetchall()

        # In kết quả
        for row in rows: 
            videoID_In_DB_After_Upload.insert(0,row[1])
            idVideoGetFromDB.append(row[0].replace("youtube-", ""))
            
        connectDB().close()  # Ngat Ket Noi

    except psycopg2.Error as e:

        print("Lỗi khi kết nối đến database:", e)
        functionSendMessageToTelegram("Lỗi khi kết nối đến database:" + e)

    if str(idVideoGetFromDB[0]) in str(ID_Video_Check_Input): return True
    else:return False
    
# Hàm ghi dữ liệu vào file txt
def writeTo_uploadedAndDeletedInfo(channel_ConfigID_Input_1,
                                   ID_Video_Input_1,
                                   title_Video_Input_1,
                                   hashtag_Video_Input_1,
                                   default_Ribbon_Input_1,
                                   default_Keyword_Input_1):

    # Ghi dữ liệu + Xử lý dư liệu thu vào

    print("Write infor to uploadedAndDeletedInfo.txt")

    with open('uploadedAndDeletedInfo.txt', 'a', encoding="utf-8") as file:

        textWrite = str(makeShortTitle(title_Video_Input_1)) + " /+/ " + str(makeShortTitle(title_Video_Input_1)) + " /+/ " + str(ID_Video_Input_1) + " /+/ " + str(hashtag_Video_Input_1) + " /+/ "\
                    + str(channel_ConfigID_Input_1) + " /+/ " + str(default_Ribbon_Input_1)  + " /+/ " + str(default_Keyword_Input_1)

        # Tại đây thêm 2 trường mới rb + keyword

        file.write(textWrite)  # Thông tin ghi vào file lưu trữ 1 => Dùng xong xóa

    time.sleep(3)
    
# Hàm ghi thông tin vào file listDownloadedVideos.txt
def writeTo_listDownloadedVideos(ID_User_Input_2, 
                                 channel_ConfigID_Input_2,
                                 ID_Video_Input_2,
                                 title_Video_Input_2,
                                 hashtag_Video_Input_2):

    # Ghi dữ liệu save lai.
    print("Save thong tin Video download")

    with open('listDownloadedVideos.txt', 'a', encoding="utf-8") as file:

        textWrite = channel_ConfigID_Input_2 + " /+/ " + str(ID_User_Input_2) + " /+/ " + str(ID_Video_Input_2) \
                    + " /+/ " + str(title_Video_Input_2) + " /+/ " + str(hashtag_Video_Input_2) + " /+/ " + str(timeCheckNow())

        file.write(textWrite + '\n')  # Thông tin ghi vào file lưu trữ 2

# Hàm ghi thông tin vào file unavailableVideosList.txt
def writeTo_unavailableVideosList(ID_User_Input, 
                                  channel_ConfigID_Input, 
                                  ID_Video_Input, 
                                  Title_Video_Input,
                                  hashtag_Video_Input):

        # Ghi dữ liệu save lai khi download khong thanh cong

        print("Save thong tin Video download => Khong Thanh Cong")

        functionSendMessageToTelegram("Video upload lên DB không thành công -> Đã lưu lại kiểm tra")

        with open('unavailableVideosList.txt', 'a', encoding="utf-8") as file:

            textWrite = channel_ConfigID_Input + " /+/ " + str(ID_User_Input) + " /+/ " + str(ID_Video_Input) \
                        + " /+/ " + str(Title_Video_Input) + " /+/ " + str(hashtag_Video_Input) + " /+/ " + str(timeCheckNow())

            file.write(textWrite + '\n')  # Thông tin ghi vào file lưu trữ 2    
            
# Hàm hỗ trợ xóa các file trong thư mục
def delete_files_in_directory_except(directory, excluded_file):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path) and filename != excluded_file:
            os.remove(file_path)
            print(f"Deleted file: {file_path}")
            
# Kiểm tra trong string có chữ " Playlist " hay không
def check_playlist_plus(input_string):
    return "playlist?" in input_string

# Hàm kiểm tra dấu /+/ có trong chuỗi hay không
def check_slash_plus(input_string):
    return "/+/" in input_string

# Hàm xử lý lấy Source Code của trang cần tải Video về
def get_Source_Code_Main(ID_USER_INPUT, Crawl_Method_Input):

        print("Get Soure Code for Daily")
        
        # Kiểm tra trong chuỗi có chữ playlist? hay không
        if check_playlist_plus(ID_USER_INPUT) == True: 
            # Nếu là playlist thì lấy link playlist
            url = 'https://www.youtube.com/' + ID_USER_INPUT
            
        else : url = 'https://www.youtube.com/@' + ID_USER_INPUT +'/videos'
        
        openLinkVideoAndDownload(url)

        # Xác định cách muốn tải Video của User này ( all / daily )

        if Crawl_Method_Input == "all": scroll_All_Video()

        # Tiến hành copy hết Source Code chính

        mouseCursorPositioning("iconHelpCopySoure_1.jpg", "Click to icon Element", 180, 20)
        time.sleep(2)
        pyautogui.press("F12")
        mouseCursorPositioning("iconHelpCopySoure_2_1.jpg", "Click to HTML Line", 15, 5)
        time.sleep(1)
        mouseCursorPositioning("iconHelpCopySoure_2.jpg", "Click to HTML Line", 15, 25)
        time.sleep(1)
        pyautogui.rightClick()
        time.sleep(1)
        mouseCursorPositioningNotClick('iconHelpCopySoure_3.jpg', "Click to Copy HTML Line", 10, 38)
        time.sleep(1)
        mouseCursorPositioningNotClick('iconHelpCopySoure_4.jpg', "Click to Copy HTML Line", 10, 5)
        time.sleep(1)
        leftClick()
        time.sleep(1)
        closeWebBrowser()
        
        # Trả ra giá trị Source Code lấy được
        return pyperclip.paste()
    
# Hàm hỗ trợ kết nối database DB để lấy dữ liệu xuống sắp xếp
def update_List_Video_Downloaded_From_DB():

    def getIDVideoFromDB():

        listData_Got = []

        cur = connectDB().cursor()

        # Hàm hỗ trợ lấy dữ liệu ChannelConfigID + ID video +thời gian tải lên
        
        cur.execute( 'SELECT "ChannelConfigID", "ReferenceSource", "Title", "CreatedDate" '
                     'FROM "Videos" WHERE "ReferenceSource" LIKE %s AND "Enable" = true ORDER BY "CreatedDate"',('youtube-%',))

        rows = cur.fetchall()

        # Lưu vào Data => Chuẩn bị tới bước tiếp theo phân loại và xóa trash

        for row in rows: listData_Got.append(row)

        for i in range((len(listData_Got))):

            valueShow = str(listData_Got[i][0]) + str(" /+/ Tên Kênh Trống /+/ ") +  str(listData_Got[i][1]).replace("youtube-", "") \
                        + str(" /+/ ") + str(listData_Got[i][2]) + str(" /+/ Từ Khóa Trống /+/ ") + str(listData_Got[i][3])

            # Ghi dữ liệu vào file txt
            with open('listDownloadedVideos.txt', 'a', encoding='utf-8') as file:
                file.write(str(valueShow)+'\n')

        # Ngắt kết nối khi lấy dữ liệu xong

        cur.close()
        connectDB().close()

    # Lấy dữ liệu từ DB PROD xuống list lưu

    getIDVideoFromDB()

# Hàm hỗ trợ xuyên suốt chương trình
def remove_Space_In_Text(string):

    string_without_spaces = string.split()
    my_string = ' '.join(string_without_spaces)

    return(my_string)

def makeShortTitle(string):

    words = string.split()  # Cắt chuỗi thành list các từ
    new_string = ""

    for word in words:
        if len(new_string) + len(word) + 1 <= 150:
            new_string += word + " "
        else:
            break

    if len(new_string) < len(string):
        new_string += "..."

    return (new_string)

def openLinkVideoAndDownload(linkUrl):

    print("Open link page: ", linkUrl)

    time.sleep(2)

    wb.get(urlChrome).open_new(linkUrl)
    
    print("Wait for load page ...")
    
    while 1:
        time.sleep(1)
        if functionCheckIconHaveOrNot('loading_page.JPG') == True: break
        
    time.sleep(5)
    
def closeWebBrowser():

    mouseCursorPositioning('exit_browser_1.jpg', 'Click turn off tab web', 15, 15)

def moveMousePosition(x, y):
    pyautogui.FAILSAFE = False
    win32api.SetCursorPos((x, y))

def pressEsc():

    for i in range(random.randint(2, 4)):
        time.sleep(1)
        pyautogui.press('esc')

def leftClick():

    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
    time.sleep(0.1)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)

def scrollMouse():

    print('Scroll Mouse =>')

    value_random_when_scroll_mouse_up = random.randint(500, 800)

    value_random_when_scroll_mouse_down = random.randint(5000, 6000)

    pyautogui.scroll(+value_random_when_scroll_mouse_up)
    time.sleep(0.5)
    pyautogui.scroll(-value_random_when_scroll_mouse_down)

# def mouseCursorPositioning(imglink, title, x, y):
    
#     # Đang sử dụng cho màn hình 1024*720

#     print(title)

#     for i in range(10):

#         time.sleep(0.25)

#         print("Loading check icon ... => ", i)
        
#         if functionCheckIconHaveOrNot(imglink) == True:

#             for pix_mop in pyautogui.locateAllOnScreen(imgUrl + imglink, confidence=confidenceImg,region=(0, 0, areaDisplayPC[0], areaDisplayPC[1])):
#                 print("==> Click")
#                 x = pix_mop[0] + x
#                 y = pix_mop[1] + y
#                 moveMousePosition(x, y)
#                 time.sleep(round(float(random.uniform(1, 2)), 2))
#                 leftClick()
#                 time.sleep(round(float(random.uniform(1, 2)), 2))
#                 # ==>
#                 break

#             break

def mouseCursorPositioning(imglink, title, x, y):
    print(f"Starting: {title}")
    print(f"Looking for image: {imglink}")

    for i in range(10):  # Retry up to 10 times
        time.sleep(0.25)
        print(f"Attempt {i+1}: Checking for icon...")

        if functionCheckIconHaveOrNot(imglink):
            print("Icon found, locating position...")
            
            try:
                matches = list(pyautogui.locateAllOnScreen(
                    imgUrl + imglink, 
                    confidence=0.7,  # Adjust confidence as needed
                    region=(0, 0, areaDisplayPC[0], areaDisplayPC[1])
                ))
                
                if not matches:
                    print("No matches found on screen.")
                    continue

                for pix_mop in matches:
                    print(f"Icon located at: {pix_mop}")
                    x_new = pix_mop[0] + x
                    y_new = pix_mop[1] + y
                    print(f"Moving mouse to: ({x_new}, {y_new})")
                    moveMousePosition(x_new, y_new)
                    time.sleep(round(float(random.uniform(1, 2)), 2))
                    print("Performing left click...")
                    leftClick()
                    time.sleep(round(float(random.uniform(1, 2)), 2))
                    break  # Stop after the first match

            except pyautogui.ImageNotFoundException:
                print("ImageNotFoundException: Could not locate the image.")

            break  # Exit retry loop after finding the image
    else:
        print(f"Failed to find image: {imglink} after 10 attempts.")



def mouseCursorPositioningNotClick(imglink, title, x, y):
    
    # Đang sử dụng cho màn hình 1024*720

    print(title)

    for i in range(20):

        time.sleep(0.5)

        print("Loading check icon ... => ", i)
        
        if functionCheckIconHaveOrNot(imglink) == True:
            for pix_mop in pyautogui.locateAllOnScreen(imgUrl + imglink,confidence=confidenceImg,region=(0, 0, areaDisplayPC[0], areaDisplayPC[1])):
                print("==> Click")
                x = pix_mop[0] + x
                y = pix_mop[1] + y
                moveMousePosition(x, y)

                break

            break

def timeCheckNow():

    now = datetime.now()
    formatted_time = now.strftime("%I:%M %p - %d/%m/%Y")
    string_time = " " + formatted_time + " "
    return (string_time)

def functionCheckIconHaveOrNot(imglink):
    print(f"Looking for image: {imglink}")
    retries = 10  # Number of retries
    for attempt in range(retries):
        try:
            print(f"Attempt {attempt + 1}/{retries}")
            match = pyautogui.locateOnScreen(
                imgUrl + imglink, 
                confidence=0.7, 
                region=(0, 0, areaDisplayPC[0], areaDisplayPC[1])
            )
            if match:
                print(f"Image found at: {match}")
                return True
        except pyautogui.ImageNotFoundException:
            print("Image not found. Retrying...")
        time.sleep(0.5)  # Add a delay between retries
    print("Failed to locate image after retries.")
    return False


# Hàm hỗ trợ xóa giá trị trong file Txt
def clear_File_uploadedAndDeletedInfo(file_Path):
    
    print("Remove value in file Txt")
    
    with open(file_Path, 'w', encoding="utf-8") as file:
        file.write("")  # Ghi chuỗi rỗng vào file để xóa hết dữ liệu
        
# Hàm hỗ trợ xóa các dữ liệu cũ để chạy vòng lặp mới
def remove_Data_For_New_Loop():
    
    print("Xóa hết dữ liệu cũ ... chạy vòng lặp mới ...")
    # Tắt các Video còn đang Download
    # close_Video_Still_Download(2)
    # Xóa dữ liệu cũ để bắt đầu vòng lặp mới
    delete_files_in_directory_except('uploadConvertVideo', 'note.txt')
    clear_File_uploadedAndDeletedInfo('uploadedAndDeletedInfo.txt')
    
# # Hàm hỗ trợ tắt các Video đang download để chạy vòng lặp mới
# def close_Video_Still_Download(qty):
    
#     print('Off các Video đang còn download ... Bắt đầu vòng lặp mới ...')
    
#     for i in range(qty): mouseCursorPositioning('stop_Download _Still_Have.JPG','Click stop Video still download', 5,5)
        
# Lấy hình thumnail của Video
def get_Thummnail_Video(ID_Video_Input_6):
    
    print("Tải hình bìa Video ...")
    
    # Đường dẫn URL của hình ảnh bạn muốn tải xuống
    file_path = 'uploadConvertVideo/'+ str(ID_Video_Input_6) + ".jpg" #str(check_extension_image(url))
    
    # Đọc video từ tập tin
    cap = cv2.VideoCapture("uploadConvertVideo/"+str(ID_Video_Input_6)+'.mp4')

    # Đọc frame đầu tiên
    ret, frame = cap.read()

    # Nếu đọc thành công
    if ret:
        # Lưu frame như hình thumbnail
        cv2.imwrite(file_path, frame)
        print(f"Thumbnail saved: {file_path}")

    # Giải phóng bộ nhớ và đóng video
    cap.release()
      
# Hàm hỗ trợ khi tương tác với Web
def scroll_All_Video():

    valueCheckScroll_Stop = []

    mouseCursorPositioning("iconHelpCopySoure_1.jpg", "Click to icon Youtube", 180, 20)
    time.sleep(2)

    print("Load all video user Page =>")

    while 1:

        print("Check make sure for load all page: ", sum(valueCheckScroll_Stop))

        scrollMouse()

        time.sleep(2)

        # Scroll tiep tuc
        
        if functionCheckIconHaveOrNot('screenshot_CheckWhenScrollFullPage.png') == True:

            print("Thay hinh giong nhau")
            valueCheckScroll_Stop.append(1)

        # Chụp ảnh tại vị trí (x, y) với kích thước (width, height)
        image = ImageGrab.grab(bbox=(753, 667, 753 + 800, 667 + 300))

        # Lưu ảnh vào tệp tin

        image.save('img/screenshot_CheckWhenScrollFullPage.png')

        # Sau do' check xem hinh hien tai co dong giong screen shot trong vong 20 - 30s, neu giong nhau => Stop scroll

        if sum(valueCheckScroll_Stop) >= 3:
            print("Scroll all page => Done")
            break

# Hàm chính chạy chương trình ----------------------------------------- /
def runProgram(ID_User_Use, channel_ConfigID_Use, crawl_Method_Use, default_Ribbon_Use, default_Keyword_Use):
    
    update_Width_Height_Video()
    
    # Khai báo kiểu giá trị 
    ID_User_Use = str(ID_User_Use)
    channel_ConfigID_Use = str(channel_ConfigID_Use)
    crawl_Method_Use = str(crawl_Method_Use)
    default_Ribbon_Use = str(default_Ribbon_Use)
    default_Keyword_Use = str(default_Keyword_Use)
    
    # Nơi lưu source code chính lấy được
    source_Code_Use = get_Source_Code_Main(ID_User_Use, crawl_Method_Use)
    
    # Function xử lý chuỗi trong source + chỉnh sửa cập nhật thông tin cho user 
    
    # Trường hợp Page có nhiều List
    if check_playlist_plus(ID_User_Use) == True:  data_IDVideo_Title_Hashtag = get_ID_Video_PlayList_Page(source_Code_Use) 
    # Trường hợp Page bình thường
    else: data_IDVideo_Title_Hashtag = get_Data_Video_Nomarl_Page(source_Code_Use)
    
    # Hàm Triển khai chương trình
    download_Video_Step_2(channel_ConfigID_Use, ID_User_Use, default_Ribbon_Use, default_Keyword_Use, data_IDVideo_Title_Hashtag)
    print ("thong tin dau vao:")
    print("channel_ConfigID_Input_4:", {channel_ConfigID_Use})
    print("id_user_4:", {ID_User_Use})
    print ("default_Ribbon_4:" ,{default_Ribbon_Use})
    print("default_keyword_5:", {default_Keyword_Use})
    print("data_IDVideo_Title_Hasgtag_Input:", data_IDVideo_Title_Hashtag)
#update_List_Video_Downloaded_From_DB()

update_Width_Height_Video()