/* Webweaver: a colossal spider, not a humanoid. All geometry is procedural. */
function createRaidBoss(){
 const bones=[],parts=[],legs=[];
 const bone=(name,parent,pos,rot)=>bones.push({name,parent,pos,...(rot?{rot}:{})});
 const add=(shape,bone,pos,size,color,rot=[0,0,0],glow=false)=>parts.push({shape,bone,pos,size,color,rot,glow});
 const box=(...a)=>add('box',...a),poly=(...a)=>add('poly',...a),shell=(...a)=>add('shell',...a),crystal=(...a)=>add('crystal',...a),fang=(...a)=>add('fang',...a);
 const P={dark:'#21192e',deep:'#130f1d',mid:'#392b49',edge:'#584563',bone:'#a99891',light:'#c7b6a8',purple:'#ac42f2',hot:'#f1a1ff',black:'#09060e'};
 bone('root',null,[0,0,0]);bone('body','root',[0,2.25,0]);bone('head','body',[0,-.18,1.35]);bone('jaw','head',[0,-.43,.4]);
 poly('body',[0,.25,-.78],[3.45,2.65,3.75],P.dark,[0,.12,0]);
 shell('body',[0,1.03,-.82],[2.7,.85,2.65],P.mid,[0,.12,0]);
 poly('body',[0,-.16,.67],[2.7,1.65,2.15],P.deep);
 shell('body',[0,.45,.5],[2.3,.72,1.8],P.mid);
 poly('body',[0,.3,-2.12],[2.05,1.45,1.15],P.mid);
 for(const side of [-1,1]){
  poly('body',[side*1.24,.35,-.72],[.82,1.5,2.15],P.mid,[0,0,side*.16]);
  poly('body',[side*.98,.98,-.38],[.78,.42,.9],P.bone,[0,side*.2,side*.18]);
  poly('body',[side*.9,.64,-1.73],[.65,.5,.82],P.edge,[0,0,side*.2]);
 }
 crystal('body',[0,1.95,-.83],[1.0,1.85,.95],P.purple,[0,0,.08]);
 crystal('body',[0,1.64,-.05],[.7,1.25,.66],P.purple,[.12,0,-.1]);
 crystal('body',[-.88,1.35,-1.05],[.62,1.05,.62],P.purple,[0,0,-.24]);
 crystal('body',[.9,1.3,-1.22],[.58,.95,.58],P.purple,[0,0,.28]);
 crystal('body',[0,.73,-2.25],[.58,.9,.55],P.purple,[.35,0,0]);
 // Four eyes and two fangs on a low spider head.
 poly('head',[0,0,0],[1.95,1.32,1.42],P.dark);
 shell('head',[0,.43,-.08],[1.65,.58,1.12],P.mid);
 poly('head',[0,.62,.2],[.72,.38,.66],P.bone,[.1,0,0]);
 for(const side of [-1,1]){
  poly('head',[side*.39,-.02,.64],[.49,.52,.24],P.black);
  poly('head',[side*.39,-.02,.755],[.29,.38,.14],P.purple,[0,0,0],true);
  poly('head',[side*.39,-.02,.825],[.13,.22,.055],P.hot,[0,0,0],true);
  poly('head',[side*.72,.23,.52],[.34,.35,.22],P.black);
  poly('head',[side*.72,.23,.625],[.18,.23,.12],P.purple,[0,0,0],true);
  poly('head',[side*.72,.23,.68],[.075,.12,.045],P.hot,[0,0,0],true);
  poly('head',[side*.63,-.36,.38],[.45,.52,.52],P.mid,[0,0,side*.12]);
  fang('jaw',[side*.43,-.32,.28],[.42,.86,.4],P.light,[.12,0,side*-.12]);
  crystal('jaw',[side*.43,-.73,.31],[.22,.38,.22],P.purple,[0,0,side*-.12]);
 }
 const rows=[1.0,.3,-.48,-1.18],splays=[.58,.2,-.2,-.62];
 for(const side of [-1,1])for(let row=0;row<4;row++){
  const s=side<0?'L':'R',upper=`leg${s}${row}`,lower=`shin${s}${row}`;
  const yaw=side>0?-splays[row]:Math.PI+splays[row];
  bone(upper,'body',[side*.83,-.12,rows[row]],[0,yaw,.34]);bone(lower,upper,[2.02,0,0],[0,0,-1.31]);legs.push(upper);
  poly(upper,[.3,0,0],[.82,.72,.78],P.mid);
  box(upper,[1.05,0,0],[1.65,.5,.55],P.deep);
  poly(upper,[1.0,.15,0],[1.32,.72,.76],P.mid);
  poly(upper,[1.63,.28,0],[.9,.64,.84],P.bone,[0,0,.08]);
  poly(upper,[2.02,0,0],[.7,.68,.72],P.light);
  box(lower,[1.12,0,0],[2.15,.48,.5],P.deep);
  poly(lower,[.52,.04,0],[1.05,.65,.7],P.mid);
  fang(lower,[1.32,0,0],[.76,1.75,.72],P.bone,[0,0,-Math.PI/2]);
  crystal(lower,[2.28,0,0],[.58,1.28,.56],P.purple,[0,0,-Math.PI/2]);
  crystal(lower,[2.84,0,0],[.3,.52,.29],P.purple,[0,0,-Math.PI/2]);
 }
 return {number:'01',name:'Webweaver',kind:'КОЛОССАЛЬНЫЙ ПАУК',description:'Огромный паук рейдовый босс с восемью лапами, четырьмя глазами и кристаллами пустоты.',accent:'#c45cff',vfx:'webweaver',vfxName:'Пустотная паутина',vfxColors:['#c354ff','#f0a4ff','#7130a8'],target:[0,1.85,.25],distance:14.8,spin:null,spider:true,rig:{body:'body',head:'head',jaw:'jaw',legs},bones,parts};
}

function buildRaidEncounter(scene){
 const group=new THREE.Group(),minionGroup=new THREE.Group();scene.add(group);group.add(minionGroup);
 const materials=new Map(),boxGeo=new THREE.BoxGeometry(1,1,1),crystalGeo=new THREE.OctahedronGeometry(.5,0);
 const mat=(color,glow=false)=>{const key=color+glow;if(!materials.has(key))materials.set(key,glow?new THREE.MeshBasicMaterial({color,toneMapped:false}):new THREE.MeshStandardMaterial({color,roughness:.82,flatShading:true}));return materials.get(key);};
 const cube=(parent,pos,size,color,rot=[0,0,0],glow=false)=>{const m=new THREE.Mesh(boxGeo,mat(color,glow));m.position.set(...pos);m.scale.set(...size);m.rotation.set(...rot);parent.add(m);return m;};
 const runeMat=new THREE.MeshBasicMaterial({color:0x8c42c7,transparent:true,opacity:.32,blending:THREE.AdditiveBlending,depthWrite:false});
 const rune=new THREE.Mesh(new THREE.RingGeometry(3.22,3.25,80),runeMat);rune.rotation.x=-Math.PI/2;rune.position.y=.018;group.add(rune);
 for(let i=0;i<16;i++){const a=i*Math.PI/8,r=3.24;const mark=cube(group,[Math.cos(a)*r,.025,Math.sin(a)*r],[.06,.018,.28],0xba68ed,[0,-a,0],true);mark.material=runeMat;}
 const minions=[];
 const spots=[[-2.45,0,1.65,.22],[2.35,0,1.55,-.3],[-2.8,0,-1.25,.6],[2.8,0,-1.15,-.55]];
 for(let index=0;index<spots.length;index++){
  const root=new THREE.Group();root.position.set(spots[index][0],0,spots[index][2]);root.rotation.y=spots[index][3];minionGroup.add(root);
  const body=new THREE.Group();body.position.y=.62;root.add(body);
  cube(body,[0,0,0],[.72,.44,.82],'#211a2a');cube(body,[0,.19,-.05],[.64,.2,.68],'#8e7e6c');
  cube(body,[0,-.02,.5],[.58,.4,.42],'#d5c29e');cube(body,[0,-.17,.69],[.46,.16,.22],'#a89579');
  for(const side of [-1,1]){
   cube(body,[side*.17,.04,.724],[.18,.17,.07],'#09070d');cube(body,[side*.17,.04,.77],[.085,.09,.04],'#d47bff',[0,0,0],true);
   cube(body,[side*.29,.21,.38],[.17,.27,.2],'#ead6ae',[0,0,side*-.3]);
  }
  const gem=new THREE.Mesh(crystalGeo,mat('#bd63ff',true));gem.position.set(0,.49,-.12);gem.scale.set(.38,.72,.38);body.add(gem);
  const legs=[];
  for(let j=0;j<6;j++){
   const side=j<3?-1:1,row=j%3,pivot=new THREE.Group();pivot.position.set(side*.3,-.03,.3-row*.32);pivot.rotation.y=side*(.55+row*.37);body.add(pivot);
   cube(pivot,[side*.25,-.04,0],[.58,.12,.14],'#baa788',[0,0,side*.25]);
   const lower=new THREE.Group();lower.position.set(side*.5,-.12,0);pivot.add(lower);
   cube(lower,[side*.1,-.22,.02],[.13,.48,.13],'#e2cda8',[0,0,side*-.35]);cube(lower,[side*.18,-.46,.08],[.12,.18,.24],'#f0dbb5',[.35,0,0]);legs.push({pivot,lower,side,row});
  }
  minions.push({root,body,legs,base:root.position.clone(),angle:spots[index][3],phase:index*1.71});
 }
 // The tiny adventurer makes the boss read as a true colossus.
 const hero=new THREE.Group();hero.position.set(.15,0,3.85);hero.rotation.y=Math.PI;group.add(hero);
 cube(hero,[0,.43,0],[.26,.38,.2],'#384357');cube(hero,[0,.72,0],[.23,.23,.23],'#d9c7a7');
 cube(hero,[0,.48,.13],[.3,.34,.06],'#633789');cube(hero,[-.09,.14,0],[.09,.3,.11],'#202534');cube(hero,[.09,.14,0],[.09,.3,.11],'#202534');
 cube(hero,[.24,.48,0],[.07,.58,.07],'#dce9f3',[0,0,-.28]);cube(hero,[.16,.25,0],[.26,.06,.09],'#9c84b5');
 return {group,minions,hero,setVisible(value){minionGroup.visible=value;},update(dt,t,state,action){
  const speed=Number(document.querySelector('#speed').value),moving=state==='walk'||state==='run',pace=state==='run'?7:state==='walk'?3.5:1.4;
  for(const m of minions){
   const phase=t*pace*speed+m.phase,attack=state==='attack'&&action?Math.sin(Math.min(1,action.time/action.getClip().duration)*Math.PI):0;
   const collapse=state==='death'&&action?Math.min(1,action.time/action.getClip().duration*1.4):0;
   const travel=moving?Math.sin(t*(state==='run'?1.1:.55)+m.phase)*(state==='run'?.48:.18):0;
   m.root.position.x=m.base.x+Math.cos(m.angle)*travel;m.root.position.z=m.base.z+Math.sin(m.angle)*travel+attack*.42;
   m.root.position.y=.12*collapse;m.root.rotation.z=state==='death'?1.28*collapse:state==='hit'?Math.sin(t*45+m.phase)*.12:0;
   m.body.position.y=.62+Math.abs(Math.sin(phase))*(moving?.09:.025)+attack*.15;m.body.rotation.x=-attack*.35;
   m.legs.forEach((leg,i)=>{leg.pivot.rotation.z=leg.side*(.08+Math.sin(phase+i*1.7)*(moving?.42:.06));leg.lower.rotation.z=leg.side*(-.12+Math.cos(phase+i*1.7)*(moving?.25:.04));});
  }
  hero.position.y=Math.sin(t*1.7)*.008;
 }};
}
