/* Ossuary and his bone crawlers. Geometry stays procedural for easy game integration. */
function createRaidBoss(){
 const bones=[],parts=[];
 const bone=(name,parent,pos,rot)=>bones.push({name,parent,pos,...(rot?{rot}:{})});
 const box=(bone,pos,size,color,rot=[0,0,0],glow=false)=>parts.push({bone,pos,size,color,rot,glow,shape:'box'});
 const crystal=(bone,pos,size,color,rot=[0,0,0],glow=true)=>parts.push({bone,pos,size,color,rot,glow,shape:'crystal'});
 const P={bone:'#d8c7a4',light:'#f1dfb8',shade:'#94836d',dark:'#17141e',armor:'#292230',iron:'#403548',purple:'#aa4dff',hot:'#efc1ff',black:'#08070c',cloth:'#392044'};
 bone('root',null,[0,0,0]);bone('body','root',[0,3.45,0]);bone('head','body',[0,1.45,.08]);bone('jaw','head',[0,-.34,.28]);
 for(const side of [-1,1]){
  const s=side<0?'L':'R';
  bone('leg'+s,'root',[side*.72,2.3,0]);bone('shin'+s,'leg'+s,[0,-1.12,0]);bone('foot'+s,'shin'+s,[0,-1.02,.08]);
  bone('arm'+s,'body',[side*1.45,.77,0]);bone('forearm'+s,'arm'+s,[side*.08,-1.18,.02]);bone('hand'+s,'forearm'+s,[0,-1.12,.08]);
 }
 // Dense torso, exposed spine and a suspended soul core.
 box('body',[0,0,-.18],[1.6,2.15,.92],P.dark);box('body',[0,.12,-.7],[.48,2.28,.38],P.armor);
 for(let i=0;i<7;i++)box('body',[0,.92-i*.31,-.93],[.58,.18,.28],i%2?P.shade:P.bone);
 box('body',[0,-1.13,-.05],[1.58,.55,1.02],P.armor);box('body',[0,-1.16,.52],[.66,.5,.2],P.bone);
 for(const side of [-1,1]){
  box('body',[side*.66,-1.15,.32],[.58,.62,.68],P.bone,[0,0,side*.18]);
  box('body',[side*.73,-1.58,.02],[.5,.68,.18],P.cloth,[0,0,side*.12]);
  for(let i=0;i<4;i++){
   const y=.73-i*.39,w=1.02-i*.07;
   box('body',[side*.48,y,.48],[w,.2,.24],i%2?P.bone:P.light,[0,side*.08,side*(-.2+i*.025)]);
   box('body',[side*(.97-i*.06),y-.14,.23],[.22,.52,.28],P.shade,[side*.18,0,side*.22]);
  }
 }
 box('body',[0,.05,.61],[.48,.82,.26],P.black);crystal('body',[0,.06,.82],[.62,1.05,.48],P.purple,[0,0,.08]);
 box('body',[0,.05,.93],[.18,.46,.09],P.hot,[0,0,.785],true);
 // Sternum, collar and layered, oversized shoulder plates.
 box('body',[0,.83,.48],[.38,.62,.3],P.light);box('body',[0,1.03,.02],[1.55,.35,.88],P.bone);
 for(const side of [-1,1]){
  const s=side<0?'L':'R',a='arm'+s,f='forearm'+s,h='hand'+s;
  box(a,[side*.04,.02,0],[1.18,.76,1.22],P.dark);
  box(a,[side*.12,.28,.02],[1.36,.42,1.34],P.bone,[0,0,side*.12]);
  box(a,[side*.36,.53,-.03],[.9,.3,1.18],P.light,[0,0,side*.22]);
  box(a,[side*.63,.18,.02],[.36,.75,1.26],P.shade,[0,0,side*.18]);
  for(let j=0;j<3;j++)crystal(a,[side*(.28+j*.25),.72+j*.14,-.25+j*.22],[.36,.92-j*.12,.36],j===1?P.light:P.bone,[0,0,side*(-.35-j*.12)],false);
  box(a,[0,-.62,0],[.72,1.18,.75],P.dark);box(a,[side*.08,-.55,.39],[.52,.92,.22],P.bone);
  box(f,[0,-.48,0],[1.02,1.18,.94],P.armor);box(f,[0,-.38,.5],[.84,.88,.22],P.bone);
  box(f,[side*.43,-.43,.02],[.24,.98,.86],P.shade);box(f,[0,-.94,0],[1.12,.28,1.02],P.light);
  for(let j=0;j<3;j++)box(f,[side*.55,-.18-j*.31,.05],[.28,.16,.76],j%2?P.shade:P.bone);
  box(h,[0,-.25,.08],[.9,.58,.82],P.dark);box(h,[0,-.18,.5],[.86,.44,.2],P.bone);
  for(let j=0;j<4;j++){
   const x=(j-1.5)*.23;
   box(h,[x,-.58,.25],[.17,.52,.2],P.shade,[.18,0,0]);box(h,[x,-.87,.37],[.14,.28,.16],P.light,[.55,0,0]);
  }
  box(h,[side*.52,-.28,.14],[.22,.55,.26],P.bone,[0,0,side*.55]);
 }
 // A grave-cleaver grows out of the right gauntlet.
 box('handR',[0,-1.18,.02],[.2,1.65,.24],P.iron);box('handR',[0,-1.82,.03],[1.34,.34,.36],P.bone);
 box('handR',[-.48,-2.28,.03],[.68,.88,.28],P.light,[0,0,-.22]);
 box('handR',[.37,-2.2,.03],[.56,.72,.28],P.shade,[0,0,.25]);
 box('handR',[-.57,-2.77,.03],[.42,.32,.2],P.light,[0,0,-.35]);
 crystal('handR',[0,-1.82,.25],[.28,.4,.18],P.purple);
 // Weighty legs and broad, clawed feet.
 for(const side of [-1,1]){
  const s=side<0?'L':'R',l='leg'+s,sh='shin'+s,f='foot'+s;
  box(l,[0,-.48,0],[.9,1.08,.88],P.dark);box(l,[0,-.36,.46],[.7,.72,.22],P.bone);
  box(l,[side*.4,-.48,0],[.22,.8,.72],P.shade);box(l,[0,-.98,.06],[1.0,.3,.96],P.light);
  box(sh,[0,-.45,0],[.78,1.04,.74],P.armor);box(sh,[0,-.39,.42],[.62,.88,.24],P.bone);
  box(sh,[0,-.72,.57],[.42,.34,.2],P.light);box(f,[0,-.12,.3],[1.02,.4,1.32],P.dark);
  box(f,[0,.02,.53],[1.04,.26,.86],P.bone);
  for(let j=0;j<3;j++)box(f,[(j-1)*.32,-.16,1.03],[.24,.24,.62],P.light,[.08,0,0]);
 }
 // Horned skull, recessed eyes and individually blocked teeth.
 box('head',[0,.05,0],[1.24,.96,1.0],P.bone);box('head',[0,.43,-.08],[1.04,.4,.88],P.light);
 box('head',[0,-.28,.36],[.86,.4,.64],P.shade);box('head',[0,.03,.53],[.28,.42,.2],P.bone);
 for(const side of [-1,1]){
  box('head',[side*.34,.14,.51],[.4,.32,.18],P.black,[0,0,side*.12]);
  box('head',[side*.34,.15,.625],[.17,.16,.08],P.purple,[0,0,side*.12],true);
  box('head',[side*.34,.15,.675],[.07,.07,.035],P.hot,[0,0,0],true);
  box('head',[side*.35,.37,.57],[.55,.18,.24],P.light,[0,0,side*-.15]);
  box('head',[side*.58,-.2,.28],[.28,.52,.48],P.bone,[0,0,side*.18]);
  box('head',[side*.58,.62,-.12],[.34,.58,.38],P.shade,[0,0,side*-.3]);
  box('head',[side*.78,.94,-.15],[.3,.58,.32],P.bone,[0,0,side*-.5]);
  box('head',[side*.98,1.25,-.17],[.24,.46,.26],P.light,[0,0,side*-.35]);
 }
 box('jaw',[0,-.14,.16],[.86,.28,.62],P.bone);box('jaw',[0,.03,.43],[.68,.18,.12],P.black);
 for(let j=0;j<5;j++)box('jaw',[(j-2)*.15,.11,.51],[.1,.25,.13],P.light);
 for(let j=0;j<4;j++)box('head',[(j-1.5)*.17,-.28,.61],[.11,.24,.13],P.light);
 crystal('head',[0,.88,-.1],[.36,.74,.36],P.purple,[0,0,0]);
 return {number:'13',name:'Ossuary',kind:'КОСТЯНОЙ КОЛОСС',description:'Громадный рейдовый босс с костяными латами и пустотным сердцем.',accent:'#c477ff',vfx:'ossuary',vfxName:'Пустотное пламя',vfxColors:['#bd63ff','#f0c2ff','#7130a8'],target:[0,2.85,.35],distance:14.6,spin:null,rig:{body:'body',head:'head',jaw:'jaw',arms:['armL','armR'],legs:['legL','legR']},bones,parts};
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
 const spots=[[-2.45,0,2.05,.22],[2.35,0,2.3,-.3],[-2.8,0,-1.25,.6],[2.8,0,-1.15,-.55]];
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
   const travel=moving?Math.sin(t*(state==='run'?1.1:.55)+m.phase)*(state==='run'?.48:.18):0;
   m.root.position.x=m.base.x+Math.cos(m.angle)*travel;m.root.position.z=m.base.z+Math.sin(m.angle)*travel+attack*.42;
   m.root.position.y=state==='death'?.12:0;m.root.rotation.z=state==='death'?1.28:state==='hit'?Math.sin(t*45+m.phase)*.12:0;
   m.body.position.y=.62+Math.abs(Math.sin(phase))*(moving?.09:.025)+attack*.15;m.body.rotation.x=-attack*.35;
   m.legs.forEach((leg,i)=>{leg.pivot.rotation.z=leg.side*(.08+Math.sin(phase+i*1.7)*(moving?.42:.06));leg.lower.rotation.z=leg.side*(-.12+Math.cos(phase+i*1.7)*(moving?.25:.04));});
  }
  hero.position.y=Math.sin(t*1.7)*.008;
 }};
}
