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
 const group=new THREE.Group();scene.add(group);
 const materials=new Map(),boxGeo=new THREE.BoxGeometry(1,1,1),crystalGeo=new THREE.OctahedronGeometry(.5,0);
 const mat=(color,glow=false)=>{const key=color+glow;if(!materials.has(key))materials.set(key,glow?new THREE.MeshBasicMaterial({color,toneMapped:false}):new THREE.MeshStandardMaterial({color,roughness:.82,flatShading:true}));return materials.get(key);};
 const cube=(parent,pos,size,color,rot=[0,0,0],glow=false)=>{const m=new THREE.Mesh(boxGeo,mat(color,glow));m.position.set(...pos);m.scale.set(...size);m.rotation.set(...rot);parent.add(m);return m;};
 const runeMat=new THREE.MeshBasicMaterial({color:0x8c42c7,transparent:true,opacity:.32,blending:THREE.AdditiveBlending,depthWrite:false});
 const rune=new THREE.Mesh(new THREE.RingGeometry(4.65,4.68,80),runeMat);rune.rotation.x=-Math.PI/2;rune.position.y=.018;group.add(rune);
 const webPoints=[];for(let i=0;i<12;i++){const a=i*Math.PI/6;webPoints.push(0,.022,0,Math.cos(a)*4.65,.022,Math.sin(a)*4.65);}
 for(const radius of [1.3,2.35,3.45,4.65])for(let i=0;i<12;i++){const a=i*Math.PI/6,b=(i+1)*Math.PI/6;webPoints.push(Math.cos(a)*radius,.022,Math.sin(a)*radius,Math.cos(b)*radius,.022,Math.sin(b)*radius);}
 const webGeo=new THREE.BufferGeometry();webGeo.setAttribute('position',new THREE.Float32BufferAttribute(webPoints,3));group.add(new THREE.LineSegments(webGeo,new THREE.LineBasicMaterial({color:0x9a52c5,transparent:true,opacity:.16,blending:THREE.AdditiveBlending,depthWrite:false})));
 // The tiny adventurer makes the boss read as a true colossus.
 const hero=new THREE.Group();hero.position.set(.15,0,3.85);hero.rotation.y=Math.PI;group.add(hero);
 cube(hero,[0,.43,0],[.26,.38,.2],'#384357');cube(hero,[0,.72,0],[.23,.23,.23],'#d9c7a7');
 cube(hero,[0,.48,.13],[.3,.34,.06],'#633789');cube(hero,[-.09,.14,0],[.09,.3,.11],'#202534');cube(hero,[.09,.14,0],[.09,.3,.11],'#202534');
 cube(hero,[.24,.48,0],[.07,.58,.07],'#dce9f3',[0,0,-.28]);cube(hero,[.16,.25,0],[.26,.06,.09],'#9c84b5');
 group.scale.setScalar(C.environmentScale||1);hero.visible=!C.isMinion;
 return {group,minions:[],hero,update(dt,t){hero.position.y=Math.sin(t*1.7)*.008;}};
}

function spiderAnimationClips(R,makeClip){
 const all=[],add=(name,duration,defs)=>all.push(makeClip(name,duration,defs));
 let t=[0,2,4],d=[{bone:R.body,times:t,pos:[[0,0,0],[0,.06,0],[0,0,0]],rot:[[0,0,0],[.015,0,.008],[0,0,0]]},{bone:R.head,times:t,rot:[[0,-.04,0],[-.025,.05,0],[0,-.04,0]]}];
 R.legs.forEach((b,i)=>{d.push({bone:b,times:t,rot:[[0,0,0],[0,i%2?.025:-.025,.035],[0,0,0]]},{bone:b.replace('leg','shin'),times:t,rot:[[0,0,0],[0,0,-.04],[0,0,0]]});});add('idle',4,d);
 for(const run of [false,true]){const dur=run?.72:1.18;t=[0,dur/4,dur/2,dur*3/4,dur];d=[{bone:R.body,times:t,pos:[[0,0,0],[0,.07,0],[0,0,0],[0,.07,0],[0,0,0]],rot:[[0,0,-.015],[0,0,.015],[0,0,-.015],[0,0,.015],[0,0,-.015]]}];
  R.legs.forEach((b,i)=>{const phase=(i+(i>=4?1:0))%2,side=i<4?-1:1,lifts=phase?[0,-.06,0,.24,0]:[0,.24,0,-.06,0],yaws=phase?[0,-.13,0,.13,0]:[0,.13,0,-.13,0];d.push({bone:b,times:t,rot:lifts.map((v,j)=>[0,yaws[j]*side,v])},{bone:b.replace('leg','shin'),times:t,rot:lifts.map(v=>[0,0,-v*.85])});});add(run?'run':'walk',dur,d);
 }
 t=[0,.35,.78,.9,1.15,1.45];d=[{bone:R.body,times:t,pos:[[0,0,0],[0,.22,-.12],[0,.38,-.2],[0,-.12,.18],[0,0,0],[0,0,0]],rot:[[0,0,0],[-.12,0,0],[-.2,0,0],[.16,0,0],[0,0,0],[0,0,0]]},{bone:R.head,times:t,rot:[[0,0,0],[-.18,0,0],[-.28,0,0],[.25,0,0],[0,0,0],[0,0,0]]},{bone:R.jaw,times:t,rot:[[0,0,0],[.3,0,0],[.65,0,0],[.7,0,0],[0,0,0],[0,0,0]]}];
 R.legs.forEach((b,i)=>{const front=i%4<2,side=i<4?-1:1,raise=front?1:.15;d.push({bone:b,times:t,rot:[[0,0,0],[0,side*.08,.45*raise],[0,side*.15,.9*raise],[0,-side*.1,-.22*raise],[0,0,0],[0,0,0]]},{bone:b.replace('leg','shin'),times:t,rot:[[0,0,0],[0,0,-.3*raise],[0,0,-.65*raise],[0,0,.18*raise],[0,0,0],[0,0,0]]});});add('attack',1.45,d);
 t=[0,.09,.22,.4,.58];d=[{bone:R.body,times:t,pos:[[0,0,0],[0,.04,-.22],[0,0,.08],[0,0,0],[0,0,0]],rot:[[0,0,0],[0,-.08,.12],[0,.05,-.06],[0,0,0],[0,0,0]]},{bone:R.head,times:t,rot:[[0,0,0],[-.18,.12,0],[.08,-.05,0],[0,0,0],[0,0,0]]}];add('hit',.58,d);
 t=[0,.35,.9,1.55,2.2];d=[{bone:R.body,times:t,pos:[[0,0,0],[0,.1,0],[0,-.55,0],[0,-1.35,0],[0,-1.35,0]],rot:[[0,0,0],[0,0,-.04],[.08,0,.08],[.16,0,.18],[.16,0,.18]]},{bone:R.head,times:t,rot:[[0,0,0],[-.18,0,0],[.2,0,0],[.42,0,.1],[.42,0,.1]]},{bone:R.jaw,times:t,rot:[[0,0,0],[.25,0,0],[.5,0,0],[.65,0,0],[.65,0,0]]}];
 R.legs.forEach((b,i)=>{const side=i<4?-1:1;d.push({bone:b,times:t,rot:[[0,0,0],[0,0,.08],[0,side*.12,.32],[0,side*.25,.62],[0,side*.25,.62]]},{bone:b.replace('leg','shin'),times:t,rot:[[0,0,0],[0,0,-.12],[0,0,-.45],[0,0,-.78],[0,0,-.78]]});});add('death',2.2,d);return all;
}
