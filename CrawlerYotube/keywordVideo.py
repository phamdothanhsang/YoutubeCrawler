import uuid
import requests
from time import sleep
import psycopg2

# Khai báo các đầu API cần sử dụng lên PROD

API_TOKEN = 'https://wapi.weallnet.com/api/TOKEN_AccessToken/GetClientAccessToken'
API_SAVE_Keyword = 'https://wapi.weallnet.com/api/Keyword/Save'
API_SAVE_VideoKeyword = 'https://wapi.weallnet.com/api/VideoKeyword/Save'

# # Khai báo các đầu API cần sử dụng lên UAT
# API_TOKEN = 'https://wapi-uat.weallnet.com/api/TOKEN_AccessToken/GetClientAccessToken'
# API_SAVE_Keyword = 'https://wapi-uat.weallnet.com/api/Keyword/Save'
# API_SAVE_VideoKeyword = 'https://wapi-uat.weallnet.com/api/VideoKeyword/Save'

# Khai báo giá trị cần dùng
KeywordID_get = []

# Kết nối với DB | Kiểm tra Data sử dụng trước khi chạy chương trình
def connectDB():
    
    conn = psycopg2.connect(
        
            # Data PROD
            host="172.16.33.100",
            port="5432",
            database="WAN_Data",
            user="wan_data",
            password="fbpSk9MPmjheVzEtR8Ax6Q4NWYa3JnqG"
            
            # # Data UAT
            # host="172.16.34.100",
            # port="5432",
            # database="WAN_Data_UAT",
            # user="wan_data",
            # password="k24KC7VyqD4byG9MEKehVZQd"      
        )
    
    return(conn)

# Khai báo Token
def getToken():
    
    try :
        r = requests.post(API_TOKEN,
                        
            # Data PROD
            
            json={
                "clientId": "WANBMS",
                "clientSecret": "QVFOGGL5ECOTJE3RZPVRR455IWAN01",
                "scope": "WANAPI"
                }
            
            # # UAT => Test
                        
            # json={
            #     "clientId": "WANBMS",
            #     "clientSecret": "QVFOGGL5ECOTJE3RZPVRR477IWAN01   ",
            #     "scope": "WANAPI"
            #     }

            )

        return r.json().get('access_token')
    
    except requests.exceptions.HTTPError as err: print(f"Http Error: {err}")
    
TOKEN = getToken() # Khởi tạo Token

# Bước 1 upload data lên bảng Keywords
def saveKeywordDTO(TOKEN, hashtag):

    try :
        sleep(1)
        # Hàm mặc định để gọi sử dụng API lưu lên DB
        requestSave = requests.post(API_SAVE_Keyword,
                                        
                    json={
                        
                        # Đưa các dữ liệu cần upload lên DB vào đây
                            
                        "Name": hashtag,
                        "CreatedBy": 'Crawler_Tiktok',
                        "code": str(uuid.uuid1()),
                        "Type": "Keyword"          

                        },
                    
                    headers={
                    "Authorization": f'Bearer {TOKEN}' # Hàm mặc định không thay đổi
                })
        
        print(f"Uploaded KeywordID successfully | Title: {hashtag}")
        keywordID = requestSave.json().get('keyword')['keywordID']
        KeywordID_get.insert(0,keywordID) # Lưu vào biến keywordID => dùng ở Bước 2 tiếp theo
        
    except requests.exceptions.HTTPError as err: print(f"{err}")     
    
# Bước 2, sau khi có KeywordID => Upload tiếp tục lên bảng Video
def saveVideoKeyword(TOKEN, KeywordID, idvideo):
    
    VideoID_DB = []
    
    # Dùng idvideo để lấy Video ID
    
    tiktok_ReferenceSource = 'tiktok-' +  str(idvideo)
    
    # Tạo cursor để thao tác với database
    
    cursor = connectDB().cursor()  # Tạo cursor để thao tác với database
    
    # Thực hiện truy vấn SQL để lấy 5 giá trị IDVideo mới nhất

    cursor.execute('SELECT "VideoID" FROM "Videos" WHERE "ReferenceSource" = %s', (tiktok_ReferenceSource,))

    rows = cursor.fetchall()
    
    # In kết quả

    for row in rows: VideoID_DB.append(row[0]) 
    
    # Chạy Transcode tại đây
    # Khởi tạo chạy chương trình
    
    try :
        
        sleep(1)
        # Hàm mặc định để gọi sử dụng API lưu lên DB
        requestSave_2 = requests.post(API_SAVE_VideoKeyword,
                                        
                    json={
                        
                        # Đưa các dữ liệu cần upload lên DB vào đây
                            
                        "KeywordID": KeywordID,
                        "VideoID": VideoID_DB[0],
                        "CreatedBy": 'Crawler_Tiktok',
                        "Name": str(uuid.uuid1())   

                        },
                    headers={
                    "Authorization": f'Bearer {TOKEN}' # Hàm mặc định không thay đổi
                })
        
        print(f"Uploaded VideoKeyword successfully | KeywordID: {KeywordID}")  
        
        cursor.close()
        connectDB().close() # Ngắt Kết Nối

        return True
           
    except requests.exceptions.HTTPError as err: print(f"{err}")   

# Done
