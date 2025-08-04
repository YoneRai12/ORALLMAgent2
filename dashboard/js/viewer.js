let ws;
const connectBtn=document.getElementById('connect');
const disconnectBtn=document.getElementById('disconnect');
const img=document.getElementById('view');
const video=document.getElementById('hls');

function isSafari(){return /^((?!chrome|android).)*safari/i.test(navigator.userAgent);}

connectBtn.onclick=()=>{
  const token=document.getElementById('token').value;
  const sess=document.getElementById('session').value;
  if(isSafari()){
    img.style.display='none';
    video.style.display='block';
    video.src=`/stream/${sess}/master.m3u8`;
    video.play();
    return;
  }
  ws=new WebSocket(`ws://${location.host}/ws/stream/${sess}?token=${token}`);
  ws.binaryType='blob';
  ws.onmessage=(ev)=>{img.src=URL.createObjectURL(ev.data);};
};

disconnectBtn.onclick=()=>{if(ws) ws.close();};
