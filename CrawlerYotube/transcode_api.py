from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from time import sleep
import requests
import psycopg2
import time
import json
from telegram_Notify import *

qty_Video_Need_Transcode = 3

# Hàm xử lý phần Transcode cho Video tải lên  
def run_Soft_Transcode_Video(idVideo_Put_In):
    
    idVideo_Put_In = str(idVideo_Put_In)
    
    # Khai báo session + khóa để tương tác với DB
    def requests_retry_session_transcode(
        retries=3,
        backoff_factor=0.3,
        status_forcelist=(500, 502, 504),
        session=None,
    ):
        session = session or requests.Session()
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def getToken_Transcode():
        
        try :
            
            # Tương tác với PROD
            r = requests.post('https://wapi.weallnet.com/api/TOKEN_AccessToken/GetClientAccessToken',
                json={
                    "clientId": "WANBMS",
                    "clientSecret": "QVFOGGL5ECOTJE3RZPVRR455IWAN01",
                    "scope": "WANAPI"
                    }
                )
            
            return r.json().get('access_token')
        
        except requests.exceptions.HTTPError as err:
            print(f"Http Error: {err}")

    def connectionDB_forTranscode():
        
        # Tương tác bên PROD
        connection = psycopg2.connect(user="wan_data",
                                password="fbpSk9MPmjheVzEtR8Ax6Q4NWYa3JnqG",
                                host="172.16.33.100",
                                port="5432",
                                database="WAN_Data")     
        
        return (connection)  

    API_TOKEN_TRANSCODE = getToken_Transcode()

    # Hàm kiểm tra giá trị đã tồn tại trong file txt hay chưa
    def check_value_in_file(value, fileName):

        with open(fileName, "r", encoding='utf-8') as file:
            for line in file:
                if value in line:
                    return True
        return False

    # Lấy hết Id Video trong file txt 
    def IdVideo_In_File_Txt(fileName):
        
        infor_Got = []
        
        with open(fileName, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()  # Loại bỏ khoảng trắng và ký tự xuống dòng từ dòng đang xét
                if line:  # Kiểm tra nếu dòng không rỗng
                    infor_Got.append(line)   
            return(infor_Got)

    # -------------------------------------------------------------- /

    # API dùng để gọi và sử dụng Transcode

    transcodeURL_get = 'https://wapi.weallnet.com/api/Transcode/StartTranscodeVideo'

    url_transcodeCallBack_get = 'https://wapi.weallnet.com/api/Transcode/TranscodeCallBack'

    # -------------------------------------------------------------- /

    # Hàm kiểm tra video đã được Transcode hay chưa trên DB
    def check_VideoID_Transcoded(VideoID_Check):
        
        infor_Got = []

        try:

            # Tạo cursor để thao tác với database
            cursor = connectionDB_forTranscode().cursor()  # Tạo cursor để thao tác với database

            # Thực hiện truy vấn SQL để lấy giá trị Transcode
            cursor.execute('SELECT "Transcode" FROM "Videos" WHERE "VideoID" = %s', (VideoID_Check,))
            rows = cursor.fetchall()
            
            # Lọc trash in DB got 
            infor_Got.insert(0,rows[0])
            
            # Xoá trash trong giá trị 
            result = infor_Got[0]
            value = str(result[0])
        
            # Ngắt kết nối
            connectionDB_forTranscode().close()
            return(value)

        except psycopg2.Error as e: print("Have error connect with database:", e)

    # Hàm kiểm tra video có bị error trong bảng VideoTranscodeHistrories hay không 
    def check_VideoID_In_VideoTranscodeHistrories(VideoID_Check):
        
        infor_Got = []

        try:

            # Tạo cursor để thao tác với database
            cursor = connectionDB_forTranscode().cursor()  # Tạo cursor để thao tác với database

            # Thực hiện truy vấn SQL để lấy giá trị Transcode
            cursor.execute('SELECT "Status" FROM "VideoTranscodeHistories" WHERE "VideoID" = %s', (VideoID_Check,))
            rows = cursor.fetchall()
            
            # Lọc trash in DB got 
            infor_Got.insert(0,rows[0])
            
            # Xoá trash trong giá trị 
            result = infor_Got[0]
            value = str(result[0])
        
            # Ngắt kết nối
            connectionDB_forTranscode().close()
            return(value)

        except psycopg2.Error as e: print("Have error connect with database:", e)
        
    # Hàm ghi dữ liệu vào file txt
    def write_idVideo_Transcode(idVideo):
        valueShow = str(idVideo)
        # Ghi dữ liệu vào file txt
        with open('idVideo_Transcode.txt', 'a', encoding='utf-8') as file:
            file.write(str(valueShow)+'\n')

    # Bước 1: Khởi tạo chạy chương trình chạy lấy Video cần Transcode --- /
    def run_Step_1_getVideoNeedTranscode(mediaType):
        
        # Tại hàm này có thể điều chỉnh số lượng Video muốn Transcode 1 lần, hiện tại là 4 video
        def queryDB_Step_1(queryType):
        
            try:
                # Tại đây bắt đầu tương tác với DB
                cursor = connectionDB_forTranscode().cursor()
                if connectionDB_forTranscode():
                    
                    print("Connect successfully!!")
                    print("# ---------------------------- /")
                    
                    # Tương tác với bảng Videos => Lọc 3 ID Videos mới nhất để kiểm tra Transcode của từng Crawler
                    
                    if queryType == 'getVideos':
                        
                        video_ids = idVideo_Put_In
                        
                        query = """
                        (
                            SELECT v."VideoID" as media_id, 'video' as media_type, v."Transcode", v."Title", v."PlayURL", v."ReleaseDate" as ReleaseDate
                            FROM "Videos" v
                            WHERE (v."Transcode" IS NULL OR v."Transcode" = '' OR v."Transcode" IN ('init', 'running')) AND v."Enable" = true 
                            AND v."IsTranscode" = false AND (v."PlayURL" ilike ('%mp4%')) 
                            AND v."VideoID" = ({})
                        )
                        """.format(video_ids)
                        
                        # -----------------------------/
                        
                        cursor.execute(query)
                        queryRecords = cursor.fetchall()
                        objMedia = []
                        return queryRecords

            except (Exception, psycopg2.Error) as error: 
                print("Error while fetching data from PostgreSQL", error)
                print("# ---------------------------- /")

            finally:
                # closing database connection.
                if connectionDB_forTranscode():
                    cursor.close()
                    connectionDB_forTranscode().close()
        
        # Hàm kết nối API và bắt đầu tiến hành Transcode
        def startTranscode_Step_1(TOKEN, type):
            
            if type == "videos":
                typeID = 'videoID'
                transcodeURL = transcodeURL_get
                objMedia = queryDB_Step_1('getVideos')
            
            s = requests.Session()
            sleep(1)
            
            # Hàm mặc định để sử dụng API transcode
            if objMedia is not None and len(objMedia) > 0:
                
                for row in objMedia:
                    try: 
                        media_id = row[0]
                        media_type = row[1]
                        title = row[3]
                        statusTranscode = row[2]
                        if (statusTranscode == 'success') or (row[4].find('.m3u8') != -1) :
                            print(f'[-] SKIP Media ({type}): {media_id} Name: {title}')
                            continue
                        print(f'---\n[+] PROCESS {title}')
                        sleep(0.5)

                        r = requests_retry_session_transcode(session=s).post(transcodeURL,
                            json={"searchparams":[{"key":typeID,"value":media_id},{"key":"userCode","value":"e9c9e0fd-f97c-4433-8aa7-d5209b7d2063"}]},
                            headers={  "Authorization": f'Bearer {TOKEN}'})
                        
                        sleep(0.5)
                        print(f"VideoID: {media_id} | Status: {r.status_code}")
                        
                        # Tại đây ghi vào file " idVideo_Transcode.txt "
                        write_idVideo_Transcode(idVideo_Put_In)
                        
                    except requests.exceptions.HTTPError as err:
                        print(f'ERROR {title} Http Error: {err}')
                        print("# -------------------------------  /")
            else: 
                print('There are no elements for Start Transcode !!')
                print("# --------------------------------------------- /")
        
        # Khởi tạo chạy chương trình
        startTranscode_Step_1(API_TOKEN_TRANSCODE, mediaType)

    # Bước 1: Hàm xử lý bước 2 Call Back update lại lên bảng DB link mới sau khi Transcode --- /   
    def run_Step_2_updateNewLinkCallBack(mediaType):
        
        # Hàm lấy dữ liệu từ DB 
        def queryDB_Step_2(queryType):
            
            try:
                cursor = connectionDB_forTranscode().cursor()
                if connectionDB_forTranscode():
                    
                    print("Connect successfully!!")
                    print("# ---------------------------- /")
                    
                    if queryType == 'proccessCallBackVideos':
                        
                        # Tại đây lấy ID video trong file txt lưu để call back kiểm tra
                        video_ids = ",".join(str(id) for id in IdVideo_In_File_Txt('idVideo_Transcode.txt')) 
                        
                        query = """
                                select vth."VideoID", vth."Log" 
                                from "VideoTranscodeHistories" vth 
                                where vth."Status" IN ('init','running','error') and vth."Log" IS NOT NULL and vth."VideoID" IN ({})  
                                """.format(video_ids)
                        # ----------------------------------/
                        
                        cursor.execute(query)
                        queryRecords = cursor.fetchall()
                        objMedia = []
                        return queryRecords
                        
            except (Exception, psycopg2.Error) as error: 
                print("Error while fetching data from PostgreSQL", error)
                print("# --------------------------------------- /")

            finally:
                # closing database connection.
                if connectionDB_forTranscode():
                    cursor.close()
                    connectionDB_forTranscode().close()
        
        # Hàm xử lý gọi API để tiến hành Transcode
        def transcodeCallBack_Step_2(TOKEN, type):
            
            url_transcodeCallBack = url_transcodeCallBack_get

            if type == "videos": objJson = queryDB_Step_2('proccessCallBackVideos')
                
            # Hàm mặc định để sử dụng API transcode
            
            if objJson is not None and len(objJson) > 0:
                
                for row in objJson:
                    sleep(1.5)
                    try :
                        media_id = row[0]
                        jsonCallback = json.loads(row[1]).get("data")
                        print(f'---\n[+] PROCESS CallBack {media_id}')
                        sleep(1)
                        callbackRequest = requests.post(url_transcodeCallBack,
                                    json=jsonCallback,
                                    headers={
                                    "Authorization": f'Bearer {TOKEN}'
                                })
                        print(f"VideoID: {media_id} | Status: {callbackRequest.status_code} | Status Transcode {callbackRequest.json().get('transcoded')} | Status {callbackRequest.json().get('status')}")
                    except requests.exceptions.HTTPError as err:
                        print(f'ERROR Callback VideoID: {media_id} Http Error: {err}') 
                        print("# ---------------------------------------------------- /")         
            
            else: 
                print('There are no items for TranscodeCallBack!!')
                print("# --------------------------------------------- /")
                
        # Khởi tạo chạy chương trình        
        transcodeCallBack_Step_2(API_TOKEN_TRANSCODE, mediaType)

    # Đang phát triển ----------------------------------------------------------/

    # Hàm xóa thông tin trong file txt
    def remove_value_from_file(value, file_path):
        
        print("Remove value: ", value, " in file ", file_path)
        
        with open(file_path, "r") as file:
            lines = file.readlines()

        with open(file_path, "w") as file:
            for line in lines:
                if line.strip() != str(value):
                    file.write(line)

    def count_VideoID_Running_Transcode(fileName):
        # Mở file .txt
        with open(fileName, 'r', encoding='utf-8') as file:
            line_count = sum(1 for line in file if line.strip())
            return(line_count)
    
    # Khởi tạo chạy chương trình ----- /
    
    if count_VideoID_Running_Transcode('idVideo_Transcode.txt') < qty_Video_Need_Transcode:
        
        print("Step 1: Call Back ID Video still have in list")
        print("# ---------------------------------- /")
        functionSendMessageToTelegram("Lấy VideoID đi Transcode => Lưu vào hàng chờ ...")
        
        print("Step 2: Take Video go to Transcode")
        print("# ---------------------------------- /")
            
        # Nếu chưa đủ 3 ID thực hiện bước đưa ID mới vào transcode
        if check_value_in_file(str(idVideo_Put_In), 'idVideo_Transcode.txt') == False:
            
            run_Step_1_getVideoNeedTranscode('videos') # Tại đây đưa ID Video mới Craw về lên Transcode
            
        else: 
            
            print("ID used for Transcode already ...")
            print("# ---------------------------------- /")
        
    else :
        
        functionSendMessageToTelegram("Đã đủ 3 VideoID trong hàng chờ ... Chờ Xíu !")
        
        while 1:
            
            print("# ---------------------------------- /")
        
            print("Step 3: After full 3 Videos runing Transcode => CallBack and check Video have done or not")
            
            print("Time wait: 10s | Just leave WHILE when in list have " + str(qty_Video_Need_Transcode) + " ID ...")
            
            time.sleep(10)
            
            if count_VideoID_Running_Transcode('idVideo_Transcode.txt') < qty_Video_Need_Transcode: 
                print("ID Video in list <" + str(qty_Video_Need_Transcode) + " get another ID Video for Transcode")
                run_Step_1_getVideoNeedTranscode('videos') # Tại đây đưa ID Video mới Craw về lên Transcode
                break
            
            # Chạy hàm call back vào bảng Video Keywords để kiểm tra trạng trái transcode xong chưa với DB
            run_Step_2_updateNewLinkCallBack('videos')
            
            # Đọc ID Video trong file Txt
            try: 
                for idVideo in IdVideo_In_File_Txt('idVideo_Transcode.txt'):
                
                    # Kiểm tra trong DB các ID trong file txt đã được transcode thành công hay chưa
                    if check_VideoID_Transcoded(idVideo) == "transcoded":
                        
                        # Nếu đã transcode rồi xoá trong file Txt
                        remove_value_from_file(idVideo, "idVideo_Transcode.txt")
                        
                    # Kiểm tra ID đó có bị error trong bảng VideoTranscodeHistrories => Loại ra hàng chờ
                    if check_VideoID_In_VideoTranscodeHistrories(idVideo) == "error":
                        
                        # Nếu đã transcode rồi xoá trong file Txt
                        remove_value_from_file(idVideo, "idVideo_Transcode.txt")
            except: ("Skip ...")
                        
# Done