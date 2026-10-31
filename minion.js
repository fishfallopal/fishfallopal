/* One Webweaver minion per exported HTML file. */
function createWebweaverMinion(id=1){
 const bones=[],parts=[],legs=[];
 const bone=(name,parent,pos,rot)=>bones.push({name,parent,pos,...(rot?{rot}:{})});
 const add=(shape,bone,pos,size,color,rot=[0,0,0],glow=false)=>parts.push({shape,bone,pos,size,color,rot,glow});
 const poly=(...a)=>add('poly',...a),shell=(...a)=>add('shell',...a),crystal=(...a)=>add('crystal',...a),fang=(...a)=>add('fang',...a);
 const variants=[['#b44cff','#efadff'],['#9c55ff','#d7b5ff'],['#d14dff','#ffb1fa'],['#8d63ff','#c9bdff']],colors=variants[(id-1)%variants.length];
 bone('root',null,[0,0,0]);bone('body','root',[0,.63,0]);bone('head','body',[0,-.06,.36]);bone('jaw','head',[0,-.18,.2]);
 poly('body',[0,.06,-.14],[.88,.66,.92],'#251a33');shell('body',[0,.27,-.17],[.68,.3,.64],'#41304e');
 poly('head',[0,0,0],[.68,.52,.58],'#1b1327');
 for(const side of [-1,1]){
  poly('head',[side*.17,.01,.285],[.25,.27,.12],'#08060d');poly('head',[side*.17,.01,.345],[.15,.19,.07],colors[0],[0,0,0],true);poly('head',[side*.17,.01,.38],[.065,.1,.025],colors[1],[0,0,0],true);
  fang('jaw',[side*.18,-.13,.13],[.15,.3,.15],'#b8a5a0');
 }
 crystal('body',[0,.57,-.18],[.34,.62,.34],colors[0],[0,0,.08]);crystal('body',[-.25,.38,-.24],[.2,.38,.2],colors[0],[0,0,-.25]);crystal('body',[.25,.38,-.24],[.2,.38,.2],colors[0],[0,0,.25]);
 const rows=[.24,.07,-.12,-.28],splays=[.6,.22,-.2,-.62];
 for(const side of [-1,1])for(let row=0;row<4;row++){
  const s=side<0?'L':'R',upper=`leg${s}${row}`,lower=`shin${s}${row}`,yaw=side>0?-splays[row]:Math.PI+splays[row];
  bone(upper,'body',[side*.25,-.04,rows[row]],[0,yaw,.32]);bone(lower,upper,[.48,0,0],[0,0,-1.25]);legs.push(upper);
  poly(upper,[.22,0,0],[.44,.2,.22],'#33243f');poly(upper,[.43,.06,0],[.25,.24,.26],'#a18d91');
  poly(lower,[.22,0,0],[.45,.18,.2],'#24182f');fang(lower,[.37,0,0],[.24,.55,.25],'#9e8b94',[0,0,Math.PI/2]);crystal(lower,[.61,0,0],[.18,.38,.18],colors[0],[0,0,-Math.PI/2]);
 }
 return {number:String(id).padStart(2,'0'),name:'Webling '+String(id).padStart(2,'0'),kind:'ПРИСПЕШНИК WEBWEAVER',description:'Маленький паук с пустотными глазами и кристаллами. Отдельный анимированный ассет.',accent:colors[0],vfx:'webling',vfxName:'Пустотные искры',vfxColors:[colors[0],colors[1],'#7130a8'],target:[0,.55,.05],distance:3.7,spin:null,spider:true,isMinion:true,vfxScale:.2,environmentScale:.22,rig:{body:'body',head:'head',jaw:'jaw',legs},bones,parts};
}
