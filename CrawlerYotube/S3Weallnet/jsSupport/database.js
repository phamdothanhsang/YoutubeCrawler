const uuid = require('uuid');
const CryptoJS = require('crypto-js');
const { QueryTypes } = require('sequelize');
const { removeVietnameseSign, capitalize, ImageScreenshot, Keyword } = require('./helper');
const moment = require('moment');

const getMediaListByChannel = async (sequelize, channelConfigID) => {

   const mediaQuery = `
    SELECT "VideoID", "Title", "CreatedDate", "ReleaseDate", "Code", "ReferenceHash", "ReferenceSource", 'video' as media_type 
    FROM "Videos" 
    WHERE "ChannelConfigID" = '${channelConfigID}' 
    UNION ALL
    SELECT "MovieID", "Title", "CreatedDate", "PublishDate", "Code", "ReferenceHash", "ReferenceSource", 'movie' as media_type
    FROM "Movies" 
    WHERE "ChannelConfigID" = '${channelConfigID}'
  `;
  
   const uploadedMedia = await sequelize.query(mediaQuery, { replacements: [], type: QueryTypes.SELECT });
   return uploadedMedia;
};

const processMedia = async (sequelize, partnerProfile, mediaInfo, mediaType, imageUrl, mediaId, referenceSource = 'youtube', tagOrder = 8) => {
    
    const columns = ['ChannelConfigID', "Name", "Title", "Description", "Duration", "PlayURL", "ImageURL", "Transcode", "Enable", "Active", 
    "CreatedBy", "CreatedDate", "ModifiedBy", "ModifiedDate", 
    "IsTranscode", 'RawPlayURL', "SearchKeyword", 'ReferenceHash', 'ReferenceSource',  "Code", "TotalComment", "TotalFavorite", "TotalView",
    "TotalViewInDay", "Label", "HasBlacklist", "TotalShare"];

    const hash = CryptoJS.MD5(`${mediaId}|youtube`).toString();

    
    const values = [ 
      partnerProfile.user.channel_config_id, mediaInfo.Name, mediaInfo.Title, 
      mediaInfo.Description,  mediaInfo.Duration, mediaInfo.PlayUrl, mediaInfo.ImageURL, 
      mediaInfo.Transcode, mediaInfo.Enable, mediaInfo.Active, mediaInfo.CreatedBy, 
      mediaInfo.CreatedDate, mediaInfo.ModifiedBy, mediaInfo.ModifiedDate, mediaInfo.IsTranscode,  
      mediaInfo.RawPlayUrl, mediaInfo.SearchKeyword, hash,`${referenceSource}-${mediaId}`,  mediaInfo.Code,
      0, 0, 0, 0, mediaInfo.Label, mediaInfo.HasBlacklist, 0];

    if (mediaType === 'movie' && mediaInfo.Title.toLowerCase().indexOf('tập') >= 0){
        columns.push('MovieType');
        columns.push('PostDate');
        values.push('episode');
    }

    if(mediaInfo.hasOwnProperty("PostDate")){

      values.push(mediaInfo.PostDate);

    }else{
      columns.push('ReleaseDate');
      values.push(mediaInfo.ReleaseDate);
    }

    let query = `INSERT INTO "${capitalize(mediaType)+"s"}"(${columns.map(item => (`"${item}"`)).join(',')}) VALUES (${columns.map(() => '?').join(',')}) `;

    if(mediaType === 'movie') {
       query += ` RETURNING "MovieID" `;
    }else{
       query += ` RETURNING "VideoID" `;
    }


    const data  = await sequelize.query(query, { replacements: values, type: QueryTypes.INSERT });

    if(data && data.length > 0){
      let objectID = data[0][0];
      let id = null;
       
      if(objectID.hasOwnProperty("VideoID")){
        id = parseInt(objectID.VideoID);             
      }else{
        id = parseInt(objectID.MovieID); 
      }

      mediaInfo.id = id;

      const posterCode = uuid.v4();
      const bannerCode = uuid.v4();
      let createdDate = moment().toDate();
      let modifiedDate = moment().toDate();
      let mediaTypeCapitalize = capitalize(mediaType);
      let createdBy = mediaTypeCapitalize+"Screenshot";
     

      let posterScreenshot = new ImageScreenshot(id, posterCode, imageUrl, 0, true, createdBy, createdDate, null, modifiedDate, null, posterCode, true, 'poster');
      let bannerScreenshot = new ImageScreenshot(id, bannerCode, imageUrl, 1, true, createdBy, createdDate, null, modifiedDate, null, bannerCode, true, 'banner');

      let posterScreenshots = [Object.values(posterScreenshot)];
      let bannerScreenshots = [Object.values(bannerScreenshot)];


      let mediaID = mediaType === 'movie' ? "MovieID" : "VideoID";


      const posterQuery = `INSERT INTO "${mediaTypeCapitalize}Screenshots"("${mediaID}", "Name", "ImageURL", "Order", "Active", "CreatedBy", "CreatedDate", "ModifiedBy", "ModifiedDate", "AltText", "Code", "Enable", "ImageType") VALUES (${posterScreenshots.map(() => '?').join(",")})`;

      await sequelize.query(posterQuery, { replacements: posterScreenshots, type: QueryTypes.INSERT });

      const bannerQuery = `INSERT INTO "${mediaTypeCapitalize}Screenshots"("${mediaID}", "Name", "ImageURL", "Order", "Active", "CreatedBy", "CreatedDate", "ModifiedBy", "ModifiedDate", "AltText", "Code", "Enable", "ImageType") VALUES (${bannerScreenshots.map(() => '?').join(",")})`;

      await sequelize.query(bannerQuery, { replacements: bannerScreenshots, type: QueryTypes.INSERT });

      if(partnerProfile.default_keyword){

        let keyword = new Keyword(partnerProfile.default_keyword,id, "", 0, true, `${mediaTypeCapitalize}`+"Keyword", createdDate, null, modifiedDate);

        let arrKeyword = [Object.values(keyword)];

        const keywordsQuery = `INSERT INTO "${mediaTypeCapitalize}Keywords"("KeywordID","${mediaID}","Name", "Order","Active", "CreatedBy", "CreatedDate", "ModifiedBy", "ModifiedDate")
        VALUES (${arrKeyword.map(() => '?').join(",")})`;

        await sequelize.query(keywordsQuery, { replacements: arrKeyword, type: QueryTypes.INSERT });

      }
  
    }

};

const processUpdateMedia = async(sequelize, fileInfo, mediaType, videoSource = 'youtube') => {
    const hash = CryptoJS.MD5(`${fileInfo.display_id}|youtube`).toString();
    const referenceSource = `${videoSource}-${fileInfo.display_id}`;
    let formatDescription = fileInfo.description.replace(/'/g,'"');
    formatDescription = formatDescription.split('\n')[0];
    const query = `UPDATE ${mediaType} SET title='${fileInfo.title}', reference_source = '${referenceSource}', description = '${formatDescription}' WHERE reference_hash = '${hash}'`;
    await sequelize.query(query, { replacements: [], type: QueryTypes.UPDATE });
};
const processUpdateRibbonOrder = async(sequelize, collectionID) => {

  const updateQuery = `UPDATE "CollectionItems" SET "Order" = "Order" + 1 WHERE "CollectionID" = '${collectionID}'`;
  await sequelize.query(updateQuery, { replacements: [], type: QueryTypes.UPDATE });
}

const getMediaBasedOnIds = async(sequelize, listIds) => {
  const listVideoId = listIds.map((id) => {
    return `'${id}'`
  });
  const selectQuery = `SELECT * FROM video WHERE id IN (${listVideoId.join(',')})`;
  const videoList = await sequelize.query(selectQuery, { replacements: [], type: QueryTypes.SELECT });
  return videoList;
}

const processImageMedia = async(sequelize, videoId, imageUrl) => {
    const posterUuid = uuid.v4();
    const bannerUuid = uuid.v4();
    const imageQuery = `
      INSERT INTO image(id, image_type, image_path)
      VALUES ('${posterUuid}', 'poster', '${imageUrl}'),
      ('${bannerUuid}', 'banner', '${imageUrl}')
    `;
    await sequelize.query(imageQuery, { replacements: [], type: QueryTypes.INSERT });
    const imageMediaQuery = `
      INSERT INTO image_video(id, image_id, video_id, image_type, image_path)
      VALUES (uuid_generate_v4(), '${posterUuid}', '${videoId}', 'poster', '${imageUrl}'),
      (uuid_generate_v4(), '${bannerUuid}', '${videoId}', 'banner' , '${imageUrl}')
    `;
    await sequelize.query(imageMediaQuery, { replacements: [], type: QueryTypes.INSERT });
}

module.exports = {
    getMediaListByChannel,
    processMedia,
    processUpdateMedia,
    processUpdateRibbonOrder,
    getMediaBasedOnIds,
    processImageMedia
};
