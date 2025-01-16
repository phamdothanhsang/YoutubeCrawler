const MAX_UPLOAD_RETRY = 3;

async function completeMultipartUpload(s3, doneParams) {
  return await new Promise((resolve, reject) => {
    s3.completeMultipartUpload(doneParams, (err, data) => {
      if (err) {
        console.log('An error occurred while completing the multipart upload');
        reject(err);
      } else {
        console.log('Final upload data:', data);
        resolve(data);
      }
    });
  });
}

async function uploadPart(s3, multipart, partParams, multipartMap, tn) {
  let tryNum = tn || 1;
  await new Promise((resolve, reject) => {
    s3.uploadPart(partParams, async function(multiErr, mData) {
      if (multiErr){
        console.log(`Upload part #${partParams.PartNumber} error:`, multiErr);
        if (tryNum < MAX_UPLOAD_RETRY) {
          console.log('Retrying upload of part: #', partParams.PartNumber);
          await uploadPart(s3, multipart, partParams, multipartMap, tryNum + 1);
        } else {
          reject(multiErr);
        }
        return;
      }
      multipartMap.Parts[this.request.params.PartNumber - 1] = {
        ETag: mData.ETag,
        PartNumber: Number(this.request.params.PartNumber)
      };
      resolve();
    });
  });
}

module.exports = {
  uploadPart,
  completeMultipartUpload
};
