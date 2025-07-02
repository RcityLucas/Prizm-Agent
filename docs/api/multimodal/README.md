# 多模态API

本文档详细描述了Prizm Agent的多模态相关API，包括图像和音频的上传、处理和获取等功能。

## 目录

- [上传图像](#上传图像)
- [上传音频](#上传音频)
- [获取上传的文件](#获取上传的文件)

## 上传图像

上传图像文件，用于在对话中包含图像内容。

### 请求

```
POST /api/multimodal/image
```

### 请求体

使用`multipart/form-data`格式：

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| image | file | 是 | 要上传的图像文件 |
| userId | string | 是 | 用户ID |
| sessionId | string | 否 | 会话ID，如果要将图像与特定会话关联 |

### 响应

```json
{
  "success": true,
  "data": {
    "image_id": "image_1234567890",
    "file_name": "example.jpg",
    "content_type": "image/jpeg",
    "size": 102400,
    "upload_time": "2023-06-25T10:30:00Z",
    "url": "/api/multimodal/files/image_1234567890"
  },
  "message": "图像上传成功"
}
```

### 错误响应

```json
{
  "success": false,
  "error": "上传图像失败的原因",
  "status_code": 400
}
```

### 前端实现示例

```javascript
// 上传图像
async function uploadImage(file, userId, sessionId = null) {
  try {
    const formData = new FormData();
    formData.append('image', file);
    formData.append('userId', userId);
    
    if (sessionId) {
      formData.append('sessionId', sessionId);
    }
    
    const response = await fetch('/api/multimodal/image', {
      method: 'POST',
      credentials: 'include',
      body: formData
    });
    
    if (response.ok) {
      const result = await response.json();
      return result.data;
    } else {
      const errorData = await response.json();
      showErrorMessage(`上传图像失败: ${errorData.error || '未知错误'}`);
      return null;
    }
  } catch (error) {
    console.error('上传图像时出错:', error);
    showErrorMessage('上传图像时出错');
    return null;
  }
}

// 图像上传按钮事件监听
document.getElementById('image-upload').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (file) {
    const userId = getCurrentUserId();
    const sessionId = getCurrentSessionId();
    
    // 显示上传中状态
    showUploadingStatus();
    
    const imageData = await uploadImage(file, userId, sessionId);
    
    // 隐藏上传中状态
    hideUploadingStatus();
    
    if (imageData) {
      // 显示图像预览
      showImagePreview(imageData);
      
      // 将图像ID添加到待发送的多模态数据中
      addMediaIdToAttachments('images', imageData.image_id);
    }
  }
});

// 显示图像预览
function showImagePreview(imageData) {
  const previewContainer = document.getElementById('media-preview-container');
  
  const imagePreview = document.createElement('div');
  imagePreview.className = 'image-preview';
  imagePreview.dataset.imageId = imageData.image_id;
  
  imagePreview.innerHTML = `
    <img src="${imageData.url}" alt="上传的图像">
    <button class="remove-btn" title="移除图像">×</button>
  `;
  
  // 添加移除按钮事件
  imagePreview.querySelector('.remove-btn').addEventListener('click', () => {
    removeMediaFromAttachments('images', imageData.image_id);
    imagePreview.remove();
  });
  
  previewContainer.appendChild(imagePreview);
  previewContainer.classList.remove('hidden');
}
```

## 上传音频

上传音频文件，用于在对话中包含音频内容。

### 请求

```
POST /api/multimodal/audio
```

### 请求体

使用`multipart/form-data`格式：

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| audio | file | 是 | 要上传的音频文件 |
| userId | string | 是 | 用户ID |
| sessionId | string | 否 | 会话ID，如果要将音频与特定会话关联 |
| transcribe | boolean | 否 | 是否自动转录音频内容，默认为false |

### 响应

```json
{
  "success": true,
  "data": {
    "audio_id": "audio_1234567890",
    "file_name": "recording.mp3",
    "content_type": "audio/mpeg",
    "size": 204800,
    "duration": 15.5,
    "upload_time": "2023-06-25T10:30:00Z",
    "url": "/api/multimodal/files/audio_1234567890",
    "transcription": "这是音频内容的转录文本。"
  },
  "message": "音频上传成功"
}
```

### 错误响应

```json
{
  "success": false,
  "error": "上传音频失败的原因",
  "status_code": 400
}
```

### 前端实现示例

```javascript
// 上传音频
async function uploadAudio(file, userId, sessionId = null, transcribe = true) {
  try {
    const formData = new FormData();
    formData.append('audio', file);
    formData.append('userId', userId);
    formData.append('transcribe', transcribe.toString());
    
    if (sessionId) {
      formData.append('sessionId', sessionId);
    }
    
    const response = await fetch('/api/multimodal/audio', {
      method: 'POST',
      credentials: 'include',
      body: formData
    });
    
    if (response.ok) {
      const result = await response.json();
      return result.data;
    } else {
      const errorData = await response.json();
      showErrorMessage(`上传音频失败: ${errorData.error || '未知错误'}`);
      return null;
    }
  } catch (error) {
    console.error('上传音频时出错:', error);
    showErrorMessage('上传音频时出错');
    return null;
  }
}

// 录音功能
let mediaRecorder;
let audioChunks = [];

// 开始录音
function startRecording() {
  navigator.mediaDevices.getUserMedia({ audio: true })
    .then(stream => {
      mediaRecorder = new MediaRecorder(stream);
      audioChunks = [];
      
      mediaRecorder.addEventListener('dataavailable', event => {
        audioChunks.push(event.data);
      });
      
      mediaRecorder.addEventListener('stop', async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/mpeg' });
        const audioFile = new File([audioBlob], 'recording.mp3', { type: 'audio/mpeg' });
        
        const userId = getCurrentUserId();
        const sessionId = getCurrentSessionId();
        
        // 显示上传中状态
        showUploadingStatus();
        
        const audioData = await uploadAudio(audioFile, userId, sessionId, true);
        
        // 隐藏上传中状态
        hideUploadingStatus();
        
        if (audioData) {
          // 显示音频预览
          showAudioPreview(audioData);
          
          // 将音频ID添加到待发送的多模态数据中
          addMediaIdToAttachments('audio', audioData.audio_id);
          
          // 如果有转录文本，自动填入输入框
          if (audioData.transcription) {
            document.getElementById('message-input').value = audioData.transcription;
          }
        }
      });
      
      mediaRecorder.start();
      showRecordingStatus();
    })
    .catch(error => {
      console.error('获取麦克风权限失败:', error);
      showErrorMessage('无法访问麦克风');
    });
}

// 停止录音
function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
    hideRecordingStatus();
    
    // 关闭媒体流
    mediaRecorder.stream.getTracks().forEach(track => track.stop());
  }
}

// 录音按钮事件监听
document.getElementById('start-recording-btn').addEventListener('click', () => {
  startRecording();
  
  // 切换按钮状态
  document.getElementById('start-recording-btn').classList.add('hidden');
  document.getElementById('stop-recording-btn').classList.remove('hidden');
});

document.getElementById('stop-recording-btn').addEventListener('click', () => {
  stopRecording();
  
  // 切换按钮状态
  document.getElementById('stop-recording-btn').classList.add('hidden');
  document.getElementById('start-recording-btn').classList.remove('hidden');
});

// 显示音频预览
function showAudioPreview(audioData) {
  const previewContainer = document.getElementById('media-preview-container');
  
  const audioPreview = document.createElement('div');
  audioPreview.className = 'audio-preview';
  audioPreview.dataset.audioId = audioData.audio_id;
  
  audioPreview.innerHTML = `
    <audio controls src="${audioData.url}"></audio>
    <div class="audio-info">
      <span class="audio-duration">${formatDuration(audioData.duration)}</span>
      ${audioData.transcription ? `<span class="audio-transcription">${audioData.transcription}</span>` : ''}
    </div>
    <button class="remove-btn" title="移除音频">×</button>
  `;
  
  // 添加移除按钮事件
  audioPreview.querySelector('.remove-btn').addEventListener('click', () => {
    removeMediaFromAttachments('audio', audioData.audio_id);
    audioPreview.remove();
  });
  
  previewContainer.appendChild(audioPreview);
  previewContainer.classList.remove('hidden');
}

// 格式化音频时长
function formatDuration(seconds) {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}
```

## 获取上传的文件

获取之前上传的多模态文件（图像或音频）。

### 请求

```
GET /api/multimodal/files/{file_id}
```

### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| file_id | string | 是 | 文件ID（image_id或audio_id） |

### 响应

直接返回文件内容，带有适当的Content-Type头。

### 错误响应

```json
{
  "success": false,
  "error": "获取文件失败的原因",
  "status_code": 404
}
```

### 前端实现示例

```javascript
// 获取文件URL
function getFileUrl(fileId) {
  return `/api/multimodal/files/${fileId}`;
}

// 在消息中显示多模态内容
function displayMultiModalContent(message) {
  let content = message.content;
  
  // 如果消息包含多模态数据
  if (message.multiModalData) {
    // 处理图像
    if (message.multiModalData.images && message.multiModalData.images.length > 0) {
      const imageContainer = document.createElement('div');
      imageContainer.className = 'message-images';
      
      message.multiModalData.images.forEach(imageId => {
        const imageUrl = getFileUrl(imageId);
        const imageElement = document.createElement('img');
        imageElement.src = imageUrl;
        imageElement.alt = '消息图像';
        imageElement.className = 'message-image';
        imageElement.addEventListener('click', () => {
          openImageViewer(imageUrl);
        });
        
        imageContainer.appendChild(imageElement);
      });
      
      return `
        <div class="message-content">${content}</div>
        ${imageContainer.outerHTML}
      `;
    }
    
    // 处理音频
    if (message.multiModalData.audio && message.multiModalData.audio.length > 0) {
      const audioContainer = document.createElement('div');
      audioContainer.className = 'message-audio';
      
      message.multiModalData.audio.forEach(audioId => {
        const audioUrl = getFileUrl(audioId);
        const audioElement = document.createElement('audio');
        audioElement.controls = true;
        audioElement.src = audioUrl;
        audioElement.className = 'message-audio-player';
        
        audioContainer.appendChild(audioElement);
      });
      
      return `
        <div class="message-content">${content}</div>
        ${audioContainer.outerHTML}
      `;
    }
  }
  
  // 如果没有多模态数据，只返回文本内容
  return `<div class="message-content">${content}</div>`;
}
```
