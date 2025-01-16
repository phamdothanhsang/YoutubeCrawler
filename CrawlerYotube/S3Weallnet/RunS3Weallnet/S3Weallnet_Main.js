const moment = require('moment');
const uuid = require('uuid');
const mime = require('mime');
const fs = require('fs');
const ffmpeg = require('fluent-ffmpeg');
const aws = require('aws-sdk');
const CryptoJS = require('crypto-js');
const { Sequelize, QueryTypes } = require('sequelize');
const { S3 } = require('../jsSupport/config');
const { uploadImage, removeVietnameseSign, uploadLocalImage, formatTime, generateSearchKeyword, CollectionItem } = require('../jsSupport/helper');
const { getMediaListByChannel, processMedia, processUpdateRibbonOrder } = require('../jsSupport/database');
const { uploadPart, completeMultipartUpload } = require('../jsSupport/s3');
const child_process = require('child_process');

// Tại đây kết nối đến Database PROD

const sequelizeMedia = new Sequelize('postgres://wan_data:fbpSk9MPmjheVzEtR8Ax6Q4NWYa3JnqG@172.16.33.100:5432/WAN_Data', {
    logging: false
});

// Dành cho UAT 

// const sequelizeMedia = new Sequelize('postgres://wan_data:k24KC7VyqD4byG9MEKehVZQd@172.16.34.100:5432/WAN_Data_UAT', {
//     logging: false
// });

// Hàm kết nối đế S3 Weallnet

const s3Client = new aws.S3(S3);

// Tại đây khai báo các biến cần sử dụng để chạy chương trình

const nameUserTiktok = "YoutubeVideo";

const urlVideoFolderName = "../../uploadConvertVideo";

// Đọc File Text lưu các dữ liệu để upload lên Database
                        
const str = fs.readFileSync('../../uploadedAndDeletedInfo.txt').toString();

const arr = str.split('/+/');
                        
// Truyền dữ liệu từ file text vào đây =>

const title = arr[0].trim();
const description = arr[1].trim();
const youtubeVideoId = arr[2].trim();
const keywordVideo = arr[3].trim();
const channelConfigID = arr[4].trim(); // Thay đổi theo từng Id user => Weallnet sẽ cấp
const defaultRibbon = arr[5].trim(); // Thay đổi theo từng Id user => Weallnet sẽ cấp
const defaultKeyword = arr[6].trim(); // Thay đổi theo từng Id user => Weallnet sẽ cấp
                        
// Đưa dữ liệu vào Profile

const PROFILE = {
    
    data: {
        user: {
            channel_config_id: channelConfigID
        },
        
        default_ribbon: defaultRibbon,
        //default_keyword: defaultKeyword,
        prefix_s3: nameUserTiktok
    }
};

const minPartSize = 1024 * 1024 * 5; // Tại đây khai báo kích thước Của 1 file
//( 1024 là kích thước của một kilobyte (KB), và 5 là số lượng KB tối thiểu cho mỗi phần. Vì vậy, kết quả sẽ là 5 MB.  ) =>

const uploadMedia = async(execPath, profile) => {
    try {
        await sequelizeMedia.authenticate();
        console.log('Connection has been established successfully.');
    } catch (error) {
        console.error('Unable to connect to the database:', error);
    }
    let ribbonId = profile.default_ribbon;
    const uploadedMedia = await getMediaListByChannel(sequelizeMedia, profile.user.channel_config_id);
    const mediaMap = {};
    const mediaHashMap = {};
    let mediaType = 'video';

    for (let i = 0; i < uploadedMedia.length; i += 1){
        if (!mediaMap[uploadedMedia[i].ReferenceSource]){
            mediaMap[uploadedMedia[i].ReferenceSource] = {};
        }

        mediaHashMap[uploadedMedia[i].ReferenceSource] = uploadedMedia[i];
    }
    try {
        fs.readdir(execPath, async (err, files) => {
			
            if (err) { console.error(err); return; }
            const infoFile = 'done.json';
            if(files.length > 0){
                for (let i = 0; i < files.length; i += 1) {
                    const file = files[i];
                    try {
                        const path = `${execPath}/${file}`;

                        const params = file.split('.');

                        const extension = params.pop();
                        const videoName = params[0];
                        
                        if ( extension !== 'mp4') { continue; }

                        const fileName = params.join('.');
                        
                        const metaInfo = await new Promise((resolve, reject) => {
                            ffmpeg.ffprobe(path, (err, data) => {
                                if (err) {
                                    reject(err);
                                    return;
                                }
                                resolve(data);
                            });
                        });


                        let duration = metaInfo.format.duration || 0
                        if(metaInfo.format.duration > 0){
                            let time = formatTime(metaInfo.format.duration);
                            let hour = (parseInt(time.hours));
                            let minute = (parseInt(time.minutes));
                            let second = (parseInt(time.seconds));
                            duration = parseInt(hour) * 3600 + parseInt(minute) * 60 + parseInt(second);

                        }
    
                        const fileMimeType = mime.getType(path);
                        
                        const youtubeReferenceId = `youtube-${youtubeVideoId}`;
                        if (mediaHashMap[youtubeReferenceId]) {
                            fs.unlinkSync(path);
                            continue;
                        }
                        
                        let thumbnailMapData = {};
                        
                        if (typeof title !== 'undefined') {
                            
                            // Tại đây xử lý hình ảnh Thumbnail Video =>
                            
                            // const thumbnailCommand = `ffmpeg -i "${execPath}/${file}" -ss 00:00:01.000 -vframes 1 "${execPath}/${youtubeVideoId}.jpg"`;
                            // child_process.execSync(thumbnailCommand);
                            
                            // thumbnailMapData[youtubeVideoId] = `${execPath}/${youtubeVideoId}.jpg`;


                            // ----------------------------------------------------------------->

                            // Tại đây sẽ lưu hình lên CND => Thêm nhiều định dạng hình khác nhau, kiêm tra các định dạng hình trong file hiện có

                            const fs = require('fs');
                            const imageFormats = ['jpeg', 'jpg', 'png']; // Các định dạng hình hiện đang sử dụng
                            let imagePath;

                            for (let i = 0; i < imageFormats.length; i++) {
                                const format = imageFormats[i];
                                imagePath = `${execPath}/${youtubeVideoId}.${format}`;

                                if (fs.existsSync(imagePath)) { 
                                    // File tồn tại, thêm đường dẫn vào thumbnailMapData và kết thúc vòng lặp
                                    thumbnailMapData[youtubeVideoId] = imagePath;
                                    break;
                                }
                            }

                            // Bắt đầu upload lên DB CND
                            
                            const imageResult = await uploadLocalImage(s3Client, profile, thumbnailMapData[youtubeVideoId], {});
                            
                            if (!imageResult) { continue; }
        
                            const key = `${profile.prefix_s3}/${mediaType}/${moment().format('YYYY-MM-DD')}/${uuid.v4()}.${extension}`;
                            const multipartParams = {
                                Bucket: 'mybucket',
                                Key: key,
                                ContentType: fileMimeType
                            };
                            const multipartMap = {
                                Parts: []
                            };
                            const uploadResult = await new Promise((resolve, reject) => {
                                s3Client.createMultipartUpload(multipartParams, (err, multipart) => {
                                    if (err) { console.error(err); return; }
                                    console.log('Got upload ID', multipart.UploadId);
                                    let partNum = 1;
                                    const stream = fs.createReadStream(path);
                                    let stackBuffer = Buffer.from([]);
                                    const promiseStack = [];
                                    stream.on('data', async (buffer) => {
                                        stackBuffer = Buffer.concat([stackBuffer, buffer]);
                                        if (stackBuffer.length < minPartSize){
                                            return;
                                        }
                                        const partParams = {
                                            Body: stackBuffer,
                                            Bucket: multipartParams.Bucket,
                                            Key: multipartParams.Key,
                                            PartNumber: String(partNum),
                                            UploadId: multipart.UploadId
                                        };
                                        stackBuffer = Buffer.from([]);
                                        promiseStack.push(uploadPart(s3Client, multipart, partParams, multipartMap));
                                        partNum += 1;
                                    });
        
                                    stream.on('end', async () => {
                                        if (stackBuffer.length > 0){
                                            const partParams = {
                                                Body: stackBuffer,
                                                Bucket: multipartParams.Bucket,
                                                Key: multipartParams.Key,
                                                PartNumber: String(partNum),
                                                UploadId: multipart.UploadId
                                            };
                                            console.log('Uploaded to part: #', partParams.PartNumber);
                                            promiseStack.push(uploadPart(s3Client, multipart, partParams, multipartMap));
                                        }
        
                                        const doneParams = {
                                            Bucket: multipartParams.Bucket,
                                            Key: multipartParams.Key,
                                            MultipartUpload: multipartMap,
                                            UploadId: multipart.UploadId
                                        };
                                        await Promise.all(promiseStack);
                                        const data = await completeMultipartUpload(s3Client, doneParams);
                                        resolve(data);
                                    });
        
                                    stream.on('error', (err) => {
                                        reject(err);
                                    });
                                });
                            });
                            
                            // Đưa các thông tin lên Database tại đây
        
                            const mediaInfo = {
                                PlayUrl: uploadResult.Location.replace(S3.s3Host, S3.cdnHost),
                                RawPlayUrl: uploadResult.Location.replace(S3.s3Host, S3.cdnHost),
                                Title: title,
                                Name: title,
                                Description: description,
                                CreatedDate: moment().toDate(),
                                Enable: true,
                                Duration: duration,
                                ChannelConfigID: profile.user.channel_config_id, // ChannelConfigID Chú ý
                                Code: uuid.v4(),
                                Label: "hot",
                                HasBlacklist: false,
                                IsTranscode: false,
                                ImageURL: null,
                                Transcode: null,
                                Active: true,
                                ModifiedBy: null,
                                ModifiedDate: moment().toDate(),
                                SearchKeyword: keywordVideo // Từ Khóa tại đây
                            };

                            if(mediaType === 'movie'){
                                mediaInfo.PostDate = moment().toDate();
                                mediaInfo.CreatedBy = "Movie";
                                mediaInfo.MovieType = mediaType;
                            }else{
                                mediaInfo.ReleaseDate = moment().toDate();
                                mediaInfo.CreatedBy = "Video";
                            }

                            await processMedia(sequelizeMedia, profile, mediaInfo, mediaType, imageResult.url, youtubeVideoId, 'youtube', 15);
                            if (ribbonId  && mediaInfo.id){
                                await processUpdateRibbonOrder(sequelizeMedia, ribbonId);
                                let collectionItem = new CollectionItem(ribbonId, null, null, null, 0, true, true, "CollectionItem" ,moment().toDate(), null,moment().toDate());
                                switch(mediaType){
                                    case "movie":
                                        collectionItem.MovieID = mediaInfo.id;
                                        break;
                                    case "video":
                                        collectionItem.VideoID = mediaInfo.id;
                                        break;
                                    case "music":
                                        collectionItem.MusicID = mediaInfo.id;
                                        break;
                                    case "musicAlbum":
                                        collectionItem.MusicAlbumID = mediaInfo.id;
                                        break;
                                }
                                
                                // Hàm xử lý insert lên Database

                                let columnCollection = Object.keys(collectionItem);
                                let valueCollection = Object.values(collectionItem);
                                const query = `
                                    INSERT INTO "CollectionItems"(${columnCollection.map((item) => (`"${item}"`)).join(',')})
                                    VALUES (${columnCollection.map(() => '?').join(',')})
                                `;
                                await sequelizeMedia.query(query, {
                                    replacements: valueCollection,
                                    type: QueryTypes.INSERT
                                });
                            }

                        }

                    } catch(ex) {
                        console.log(ex);
                    }
                }
            }

        });
    }catch(e){
        console.error(e);
    }
};

(async() => { await uploadMedia(urlVideoFolderName, PROFILE.data);})();