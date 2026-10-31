/* Four related Webweaver minions, exported as four independent HTML files. */
function createWebweaverMinion(id=1){
 const bones=[],parts=[],legs=[];
 const bone=(name,parent,pos,rot)=>bones.push({name,parent,pos,...(rot?{rot}:{})});
 const add=(shape,bone,pos,size,color,rot=[0,0,0],glow=false)=>parts.push({shape,bone,pos,size,color,rot,glow});
 const box=(...a)=>add('box',...a),poly=(...a)=>add('poly',...a),shell=(...a)=>add('shell',...a),crystal=(...a)=>add('crystal',...a),fang=(...a)=>add('fang',...a);
 const variants=[
  {name:'Webling 01',kind:'ПУСТОТНЫЙ РАЗВЕДЧИК',role:'Разведчик',description:'Быстрый и лёгкий брат: узкий панцирь, длинные лапы и три тонких кристалла.',colors:['#b44cff','#efadff'],abdomen:[.8,.56,1.0],armor:[.58,.24,.72],head:[.62,.48,.56],upper:.54,lower:.62,thick:.85,bodyY:.66,bodyZ:-.2},
  {name:'Webling 02',kind:'ПУСТОТНЫЙ СТРАЖ',role:'Страж',description:'Тяжёлый бронированный брат: широкий панцирь, массивные суставы и короткие кристаллы.',colors:['#9c55ff','#d7b5ff'],abdomen:[1.14,.82,1.0],armor:[1.0,.4,.82],head:[.82,.62,.64],upper:.45,lower:.51,thick:1.35,bodyY:.7,bodyZ:-.14},
  {name:'Webling 03',kind:'ПУСТОТНЫЙ ЖАЛОНОСЕЦ',role:'Жалоносец',description:'Игольчатый брат: вытянутое тело, очень длинные лапы, острые клыки и кристальные шипы.',colors:['#d14dff','#ffb1fa'],abdomen:[.66,.55,1.18],armor:[.48,.22,.9],head:[.55,.42,.6],upper:.62,lower:.74,thick:.7,bodyY:.72,bodyZ:-.28},
  {name:'Webling 04',kind:'КОСТЯНОЙ ВЕБЛИНГ',role:'Ревенант',description:'Старший брат: костяные латы, роговые пластины, большие клыки и расколотый кристалл.',colors:['#8d63ff','#c9bdff'],abdomen:[.96,.72,1.02],armor:[.86,.34,.82],head:[.75,.56,.64],upper:.52,lower:.57,thick:1.15,bodyY:.67,bodyZ:-.18}
 ];
 const v=variants[(id-1)%variants.length],colors=v.colors;
 bone('root',null,[0,0,0]);bone('body','root',[0,v.bodyY,0]);bone('head','body',[0,-.06,.4]);bone('jaw','head',[0,-.18,.22]);
 poly('body',[0,.06,v.bodyZ],v.abdomen,id===4?'#312735':'#251a33');shell('body',[0,v.abdomen[1]*.42,v.bodyZ-.02],v.armor,id===4?'#8e7a82':'#41304e');
 poly('head',[0,0,0],v.head,id===4?'#302432':'#1b1327');
 for(const side of [-1,1]){
  const eyeX=v.head[0]*.25;
  poly('head',[side*eyeX,.01,v.head[2]*.48],[v.head[0]*.35,v.head[1]*.5,.12],'#08060d');
  poly('head',[side*eyeX,.01,v.head[2]*.59],[v.head[0]*.22,v.head[1]*.35,.07],colors[0],[0,0,0],true);
  poly('head',[side*eyeX,.01,v.head[2]*.65],[v.head[0]*.09,v.head[1]*.2,.025],colors[1],[0,0,0],true);
  fang('jaw',[side*v.head[0]*.25,-.13,.13],[.15,id===3?.48:id===2?.36:.3,.15],id===4?'#d8c2ab':'#b8a5a0',[0,0,side*-.1]);
 }
 // Each sibling has a different crystal crown and armor silhouette.
 if(id===1){
  crystal('body',[0,.61,-.26],[.25,.68,.25],colors[0],[.1,0,.05]);
  crystal('body',[-.27,.39,-.34],[.16,.42,.16],colors[0],[.15,0,-.3]);crystal('body',[.27,.39,-.34],[.16,.42,.16],colors[0],[.15,0,.3]);
 }else if(id===2){
  crystal('body',[0,.65,-.14],[.44,.52,.42],colors[0]);crystal('body',[-.36,.49,-.3],[.3,.38,.3],colors[0]);crystal('body',[.36,.49,-.3],[.3,.38,.3],colors[0]);
  for(const side of [-1,1]){shell('body',[side*.47,.18,-.14],[.4,.42,.72],'#746279',[0,0,side*.18]);box('head',[side*.3,.28,-.03],[.32,.18,.5],'#827080',[0,0,side*.18]);}
 }else if(id===3){
  crystal('body',[0,.64,-.12],[.22,.88,.22],colors[0],[.18,0,0]);crystal('body',[0,.48,-.5],[.2,.62,.2],colors[0],[.45,0,0]);crystal('body',[0,.32,-.76],[.16,.46,.16],colors[0],[.6,0,0]);
  fang('head',[0,.32,.02],[.16,.42,.16],'#c2a6aa');
 }else{
  crystal('body',[-.08,.61,-.2],[.34,.65,.32],colors[0],[.12,0,-.14]);crystal('body',[.13,.51,-.24],[.22,.38,.23],colors[0],[-.12,0,.22]);
  for(const side of [-1,1]){shell('body',[side*.38,.28,-.25],[.48,.34,.72],'#b5a096',[0,0,side*.18]);fang('head',[side*.3,.3,-.08],[.18,.44,.18],'#c8b09d',[0,0,side*-.35]);}
 }
 const rows=[.27,.08,-.13,-.3],splays=[.6,.22,-.2,-.62];
 for(const side of [-1,1])for(let row=0;row<4;row++){
  const s=side<0?'L':'R',upper=`leg${s}${row}`,lower=`shin${s}${row}`,yaw=side>0?-splays[row]:Math.PI+splays[row],t=v.thick;
  bone(upper,'body',[side*v.head[0]*.42,-.04,rows[row]],[0,yaw,.32]);bone(lower,upper,[v.upper,0,0],[0,0,-1.25]);legs.push(upper);
  poly(upper,[v.upper*.46,0,0],[v.upper*.88,.2*t,.22*t],'#33243f');
  poly(upper,[v.upper*.88,.06,0],[.25*t,.24*t,.26*t],id===4?'#c0aa97':'#a18d91');
  if(id===2||id===4)shell(upper,[v.upper*.54,.1,0],[v.upper*.7,.22*t,.32*t],id===4?'#b9a396':'#736074');
  poly(lower,[v.lower*.36,0,0],[v.lower*.72,.18*t,.2*t],'#24182f');
  fang(lower,[v.lower*.6,.035,0],[.24*t,v.lower*.85,.25*t],id===4?'#c2aa98':'#9e8b94',[0,0,Math.PI/2]);
  crystal(lower,[v.lower+.05,0,0],[.18*t,.34,.18*t],colors[0],[0,0,-Math.PI/2]);
 }
 return {number:String(id).padStart(2,'0'),name:v.name,kind:v.kind,description:v.description,accent:colors[0],vfx:'webling',vfxName:v.role+' / пустотные искры',vfxColors:[colors[0],colors[1],'#7130a8'],target:[0,v.bodyY*.9,.05],distance:id===3?4.2:id===2?3.8:3.9,spin:null,spider:true,isMinion:true,vfxScale:.2,environmentScale:.22,rig:{body:'body',head:'head',jaw:'jaw',legs},bones,parts};
}
