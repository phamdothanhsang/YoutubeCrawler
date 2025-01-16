const axios = require('axios').default;
const moment = require('moment');
const sharp = require('sharp');
const uuid = require('uuid');
const fs = require('fs');
const mime = require('mime');
const { S3 } = require('./config');
const sizeOf = require('image-size');
const MIME_TYPE = {
    JPEG: 'image/jpeg',
    PNG: 'image/png',
    WEBP: 'image/webp'
};
const child_process = require('child_process');

const ffmpegResize = async function(s3Client, partnerProfile, videoPath, execPath, fileInfo ) {
    let localImagePath = `${execPath}/${fileInfo.display_id}.jpg`;
    const buffer = fs.readFileSync(localImagePath);
    let dimension = sizeOf(localImagePath);

    const imageBuffer = {};
    const ratio = {small: 0.4, medium: 0.6, large: 0.8};
    let fileMimeType = MIME_TYPE.JPEG;
    
    const smallWidth = parseInt(dimension.width * ratio.small) ;
    const smallImageCommand = `ffmpeg -i "${videoPath}" -ss 00:00:01.000 -vframes 1 -vf scale=${smallWidth}:-1 "${execPath}/${fileInfo.display_id}_small.jpg"`;
    child_process.execSync(smallImageCommand);
    imageBuffer.small = fs.readFileSync(`${execPath}/${fileInfo.display_id}_small.jpg`);

    const mediumWidth = parseInt(dimension.width * ratio.medium) ;
    const mediumImageCommand = `ffmpeg -i "${videoPath}" -ss 00:00:01.000 -vframes 1 -vf scale=${mediumWidth}:-1 "${execPath}/${fileInfo.display_id}_medium.jpg"`;
    child_process.execSync(mediumImageCommand);
    imageBuffer.medium = fs.readFileSync(`${execPath}/${fileInfo.display_id}_medium.jpg`);

    const largeWidth = parseInt(dimension.width * ratio.large) ;
    const largeImageCommand = `ffmpeg -i "${videoPath}" -ss 00:00:01.000 -vframes 1 -vf scale=${largeWidth}:-1 "${execPath}/${fileInfo.display_id}_large.jpg"`;
    child_process.execSync(largeImageCommand);
    imageBuffer.large = fs.readFileSync(`${execPath}/${fileInfo.display_id}_large.jpg`);

    const imageUuid = uuid.v4();
    for (let k in imageBuffer) {
        const buffer = imageBuffer[k];
        const uploadParam = {
            Body: buffer,
            Bucket: 'mybucket',
            Key: `${partnerProfile.prefix_s3}/images/${moment().format('YYYY-MM-DD')}/${imageUuid}_${k}.jpg`,
            ACL: 'public-read',
            ContentType: fileMimeType
        };
        await s3Client.upload(uploadParam).promise();
    }

    const params = {
        Body: buffer,
        Bucket: 'mybucket',
        Key: `${partnerProfile.prefix_s3}/images/${moment().format('YYYY-MM-DD')}/${imageUuid}.jpg`,
        ACL: 'public-read',
        ContentType: fileMimeType
    };

    const originalImage = await s3Client.upload(params).promise();
    fs.unlinkSync(localImagePath);
    fs.unlinkSync(`${execPath}/${fileInfo.display_id}_small.jpg`);
    fs.unlinkSync(`${execPath}/${fileInfo.display_id}_medium.jpg`);
    fs.unlinkSync(`${execPath}/${fileInfo.display_id}_large.jpg`);
    return {
        url: originalImage.Location.replace(S3.s3Host, S3.cdnHost)
    };

}


const uploadLocalImage = async function(s3Client, partnerProfile, localImagePath, dimension, compress = true) {
    const buffer = fs.readFileSync(localImagePath);
    dimension = sizeOf(localImagePath);
    let newDimension = { width: dimension.width, height: dimension.height };
    
    const ratio = { small: 0.4, medium: 0.6, large: 0.8 };
    if (compress) {
        if (dimension.width < 500 || dimension.height < 500) {
            ratio.small = 0.6;
            ratio.medium = 0.7;
            ratio.large = 0.8;
        }
    } else {
        ratio.small = 1;
        ratio.medium = 1;
        ratio.large = 1;
    }
    
    const imageBuffer = {};
    let fileMimeType = MIME_TYPE.JPEG;
    
    const smallBuffer = await sharp(buffer).resize(parseInt(newDimension.width * ratio.small), parseInt(newDimension.height * ratio.small)).jpeg({quality : 100}).toBuffer();
    imageBuffer.small = smallBuffer;

    const mediumBuffer = await sharp(buffer).resize(parseInt(newDimension.width * ratio.medium), parseInt(newDimension.height * ratio.medium)).jpeg({quality : 95}).toBuffer();
    imageBuffer.medium = mediumBuffer;

    const largeBuffer = await sharp(buffer).resize(parseInt(newDimension.width * ratio.large), parseInt(newDimension.height * ratio.large)).jpeg({quality : 90}).toBuffer();
    imageBuffer.large = largeBuffer;

    const imageUuid = uuid.v4();
    for (let k in imageBuffer) {
        const buffer = imageBuffer[k];
        const uploadParam = {
            Body: buffer,
            Bucket: 'mybucket',
            Key: `${partnerProfile.prefix_s3}/images/${moment().format('YYYY-MM-DD')}/${imageUuid}_${k}.jpg`,
            ACL: 'public-read',
            ContentType: fileMimeType
        };
        await s3Client.upload(uploadParam).promise();
    }

    const params = {
        Body: buffer,
        Bucket: 'mybucket',
        Key: `${partnerProfile.prefix_s3}/images/${moment().format('YYYY-MM-DD')}/${imageUuid}.jpg`,
        ACL: 'public-read',
        ContentType: fileMimeType
    };

    const originalImage = await s3Client.upload(params).promise();
    fs.unlinkSync(localImagePath);
    return {
        url: originalImage.Location.replace(S3.s3Host, S3.cdnHost)
    };
}

const uploadImage = async function(s3Client, partnerProfile, imageUrl, dimension, compress = true) {
    const nonQueryStringUrl = imageUrl.split('?').shift();
    const response = await axios.get(imageUrl, {
        responseType: 'stream'
    });
    let fileMimeType = mime.getType(nonQueryStringUrl);
    let fileExtension = 'jpg';
    if (fileMimeType === MIME_TYPE.PNG){
        fileExtension = 'png';
    }else if (fileMimeType === MIME_TYPE.WEBP){
        fileMimeType = MIME_TYPE.JPEG;
    }
    const fileName = `${uuid.v4()}.${fileExtension}`;
    const writer = fs.createWriteStream(`./temp/${fileName}`);
    await new Promise((resolve, reject) => {
        response.data.pipe(writer);
        writer.on('error', err => {
            writer.close();
            reject(err);
        });
        writer.on('close', () => {
            resolve(true);
        });
    });
    const buffer = fs.readFileSync(`./temp/${fileName}`);
    dimension = sizeOf(`./temp/${fileName}`);
    let newDimension = { width: dimension.width, height: dimension.height };
    
    const ratio = { small: 0.4, medium: 0.6, large: 0.8 };
    if (compress) {
        if (dimension.width < 500 || dimension.height < 500) {
            ratio.small = 0.6;
            ratio.medium = 0.7;
            ratio.large = 0.8;
        }
    } else {
        ratio.small = 1;
        ratio.medium = 1;
        ratio.large = 1;
    }

    const imageBuffer = {};
    if (fileMimeType === MIME_TYPE.PNG){
        const smallBuffer = await sharp(buffer).resize(parseInt(newDimension.width * ratio.small), parseInt(newDimension.height * ratio.small)).png().toBuffer();
        imageBuffer.small = smallBuffer;

        const mediumBuffer = await sharp(buffer).resize(parseInt(newDimension.width * ratio.medium), parseInt(newDimension.height * ratio.medium)).png().toBuffer();
        imageBuffer.medium = mediumBuffer;

        const largeBuffer = await sharp(buffer).resize(parseInt(newDimension.width * ratio.large), parseInt(newDimension.height * ratio.large)).png().toBuffer();
        imageBuffer.large = largeBuffer;
    }else if (fileMimeType === MIME_TYPE.JPEG){
        const smallBuffer = await sharp(buffer).resize(parseInt(newDimension.width * ratio.small), parseInt(newDimension.height * ratio.small)).jpeg().toBuffer();
        imageBuffer.small = smallBuffer;

        const mediumBuffer = await sharp(buffer).resize(parseInt(newDimension.width * ratio.medium), parseInt(newDimension.height * ratio.medium)).jpeg().toBuffer();
        imageBuffer.medium = mediumBuffer;

        const largeBuffer = await sharp(buffer).resize(parseInt(newDimension.width * ratio.large), parseInt(newDimension.height * ratio.large)).jpeg().toBuffer();
        imageBuffer.large = largeBuffer;
    }else if (fileMimeType === MIME_TYPE.WEBP){
        const smallBuffer = await sharp(buffer).resize(parseInt(newDimension.width * ratio.small), parseInt(newDimension.height * ratio.small)).jpeg().toBuffer();
        imageBuffer.small = smallBuffer;

        const mediumBuffer = await sharp(buffer).resize(parseInt(newDimension.width * ratio.medium), parseInt(newDimension.height * ratio.medium)).jpeg().toBuffer();
        imageBuffer.medium = mediumBuffer;

        const largeBuffer = await sharp(buffer).resize(parseInt(newDimension.width * ratio.large), parseInt(newDimension.height * ratio.large)).jpeg().toBuffer();
        imageBuffer.large = largeBuffer;
    }

    const imageUuid = uuid.v4();
    for (let k in imageBuffer) {
        const buffer = imageBuffer[k];
        const uploadParam = {
            Body: buffer,
            Bucket: 'mybucket',
            Key: `${partnerProfile.prefix_s3}/images/${moment().format('YYYY-MM-DD')}/${imageUuid}_${k}.${fileExtension}`,
            ACL: 'public-read',
            ContentType: fileMimeType
        };
        await s3Client.upload(uploadParam).promise();
    }

    const params = {
        Body: buffer,
        Bucket: 'mybucket',
        Key: `${partnerProfile.prefix_s3}/images/${moment().format('YYYY-MM-DD')}/${imageUuid}.${fileExtension}`,
        ACL: 'public-read',
        ContentType: fileMimeType
    };

    const originalImage = await s3Client.upload(params).promise();
    fs.unlinkSync(`./temp/${fileName}`);
    return {
        url: originalImage.Location.replace(S3.s3Host, S3.cdnHost)
    };
};

const removeVietnameseSign = (str) => {
    if (typeof str !== 'string'){
        return null;
    }

    str = str.replace(/(á|à|ả|ã|ạ|ă|ắ|ằ|ẳ|ẵ|ặ|â|ấ|ầ|ẩ|ẫ|ậ)/g, 'a');
    str = str.replace(/(A|À|Ả|Ã|Ạ|Ă|Ắ|Ằ|Ẳ|Ẵ|Ặ|Â|Ấ|Ầ|Ẩ|Ẫ|Ậ)/g, 'A');
    str = str.replace(/đ/g, 'd');
    str = str.replace(/Đ/g, 'D');
    str = str.replace(/(é|è|ẻ|ẽ|ẹ|ê|ế|ề|ể|ễ|ệ)/g, 'e');
    str = str.replace(/(É|È|Ẻ|Ẽ|Ẹ|Ê|Ế|Ề|Ể|Ễ|Ệ)/g, 'E');
    str = str.replace(/(í|ì|ỉ|ĩ|ị)/g, 'i');
    str = str.replace(/(Í|Ì|Ỉ|Ĩ|Ị)/g, 'I');
    str = str.replace(/(ó|ò|ỏ|õ|ọ|ô|ố|ồ|ổ|ỗ|ộ|ơ|ớ|ờ|ở|ỡ|ợ)/g, 'o');
    str = str.replace(/(Ó|Ò|Ỏ|Õ|Ọ|Ô|Ố|Ồ|Ổ|Ỗ|Ộ|Ơ|Ớ|Ờ|Ở|Ỡ|Ợ)/g, 'O');
    str = str.replace(/(ú|ù|ủ|ũ|ụ|ư|ứ|ừ|ử|ữ|ự)/g, 'u');
    str = str.replace(/(Ú|Ù|Ủ|Ũ|Ụ|Ư|Ứ|Ừ|Ử|Ữ|Ự)/g, 'U');
    str = str.replace(/(ý|ỳ|ỷ|ỹ|ỵ)/g, 'y');
    str = str.replace(/(Ý|Ỳ|Ỷ|Ỹ|Ỵ)/g, 'Y');

    return str;
};


const generateSearchKeyword = function(searchKeyword){
    if(searchKeyword){
        let tempSearchKeyword = removeVietnameseSign(searchKeyword);
        tempSearchKeyword =  tempSearchKeyword.toLowerCase().toString();
        tempSearchKeyword =  tempSearchKeyword.replace(/[^a-zA-Z ]/g, "");
        tempSearchKeyword = tempSearchKeyword.replace(/\s+/g,"");
        return tempSearchKeyword;
    }
}

const capitalize = function(str){
  if (typeof str !== 'string') return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}

const formatTime = function(duration){
    const result = new Date(duration * 1000).toISOString().substr(11, 8);
    return {
        hours: result.substr(0, 2),
        minutes: result.substr(3, 2),
        seconds: result.substr(6, 2)
    }
}

const ImageScreenshot = function(Id, Name, ImageURL, Order, Active, CreatedBy, CreatedDate, 
ModifiedBy, ModifiedDate, AltText, Code, Enable, ImageType){
    this.Id = Id,
    this.Name = Name,
    this.ImageURL = ImageURL,
    this.Order = Order,
    this.Active = Active,
    this.CreatedBy = CreatedBy,
    this.CreatedDate = CreatedDate,
    this.ModifiedBy = ModifiedBy,
    this.ModifiedDate = ModifiedDate,
    this.AltText = AltText,
    this.Code = Code,
    this.Enable = Enable,
    this.mageType = ImageType
}

const Keyword = function(KeywordID, VideoID, Name, Order, Active, CreatedBy, CreatedDate, 
    ModifiedBy, ModifiedDate){
    this.KeywordID = KeywordID,
    this.VideoID = VideoID,
    this.Name = Name,
    this.Order = Order,
    this.Active = Active,
    this.CreatedBy = CreatedBy,
    this.CreatedDate = CreatedDate,
    this.ModifiedBy = ModifiedBy,
    this.ModifiedDate = ModifiedDate
}

const CollectionItem = function(CollectionID, MovieID, MusicID, VideoID, Order, Enable, Active, CreatedBy, CreatedDate, 
    ModifiedBy, ModifiedDate, MusicAlbumID){
    this.CollectionID = CollectionID,
    this.MovieID = MovieID,
    this.MusicID = MusicID,
    this.VideoID = VideoID,
    this.Order = Order,
    this.Enable = Enable,
    this.Active = Active,
    this.CreatedBy = CreatedBy,
    this.CreatedDate = CreatedDate,
    this.ModifiedBy = ModifiedBy,
    this.ModifiedDate = ModifiedDate,
    this.MusicAlbumID = MusicAlbumID
}

module.exports = {
    uploadImage,
    removeVietnameseSign,
    uploadLocalImage,
    ffmpegResize,
    generateSearchKeyword,
    capitalize,
    formatTime,
    ImageScreenshot,
    Keyword,
    CollectionItem
};
