// Sentara — Skrip menambah 3 layar alur ke file Figma (zqhukxNFG7GJHCe2SYyIYR)
// Menambah: 00 Akses Aplikasi (Landing), 05 Ekspor & Unduh, 06 Tentang & Cara Pakai.
// Skrip membaca token warna & font dari frame yang sudah ada agar konsisten.
// Cara pakai: jalankan ulang lewat Figma MCP (use_figma) saat limit Starter sudah reset,
// ATAU tempel ke plugin Figma yang punya akses figma global. Posisi frame:
//   00 di x=-1560 (kiri Dashboard), 05 di x=6240, 06 di x=7800 (mengikuti urutan alur).
return (async ()=>{
function hex(h){h=h.replace('#','');return{r:parseInt(h.slice(0,2),16)/255,g:parseInt(h.slice(2,4),16)/255,b:parseInt(h.slice(4,6),16)/255};}
function solid(c){return [{type:'SOLID',color:{r:c.r,g:c.g,b:c.b}}];}
function tint(c,a){return {r:c.r*a+(1-a),g:c.g*a+(1-a),b:c.b*a+(1-a)};}
const white=hex('#FFFFFF');
async function fs(id,prop){try{const n=await figma.getNodeByIdAsync(id);if(!n)return null;let a=n[prop];if(!a||a===figma.mixed)return null;const p=a.find(x=>x.type==='SOLID'&&x.visible!==false);return p?{r:p.color.r,g:p.color.g,b:p.color.b}:null;}catch(e){return null;}}
const T={};
T.bg=await fs('3:2','fills')||hex('#F4F5F7');
T.surface=await fs('3:31','fills')||white;
T.border=await fs('3:31','strokes')||hex('#E6E8EB');
T.text=await fs('3:6','fills')||hex('#1A1D21');
T.textSub=await fs('3:29','fills')||hex('#6B7280');
T.accent=await fs('3:5','fills')||hex('#FF4B4B');
T.pos=await fs('3:56','fills')||hex('#16A34A');
T.neu=await fs('3:58','fills')||hex('#D97706');
T.neg=await fs('3:60','fills')||hex('#DC2626');
let fam='Inter';
try{const t=await figma.getNodeByIdAsync('3:6');if(t&&t.fontName&&t.fontName!==figma.mixed)fam=t.fontName.family;}catch(e){}
const loaded=new Set();
for(const s of ['Regular','Medium','Semi Bold','Bold']){try{await figma.loadFontAsync({family:fam,style:s});loaded.add(s);}catch(e){}}
if(loaded.size===0){fam='Inter';for(const s of ['Regular','Medium','Semi Bold','Bold']){try{await figma.loadFontAsync({family:fam,style:s});loaded.add(s);}catch(e){}}}
function fnt(s){if(loaded.has(s))return{family:fam,style:s};if(loaded.has('Regular'))return{family:fam,style:'Regular'};return{family:fam,style:[...loaded][0]};}
function place(n,x,y){n.x=x;n.y=y;return n;}
function txt(s,size,style,color,parent){const t=figma.createText();t.fontName=fnt(style);t.characters=s;t.fontSize=size;t.fills=solid(color);t.lineHeight={value:Math.round(size*1.4),unit:'PIXELS'};if(parent)parent.appendChild(t);return t;}
function txtW(s,size,style,color,parent,w){const t=txt(s,size,style,color,null);t.textAutoResize='HEIGHT';t.resize(w,t.height);if(parent)parent.appendChild(t);return t;}
function rrect(w,h,color,r,parent){const x=figma.createRectangle();x.resize(w,h);x.fills=solid(color);if(r)x.cornerRadius=r;if(parent)parent.appendChild(x);return x;}
function ell(d,color,parent){const e=figma.createEllipse();e.resize(d,d);e.fills=solid(color);if(parent)parent.appendChild(e);return e;}
const shadowSm=[{type:'DROP_SHADOW',color:{r:0,g:0,b:0,a:0.06},offset:{x:0,y:1},radius:2,spread:0,visible:true,blendMode:'NORMAL'}];
function card(w,h,parent){const c=figma.createFrame();c.resize(w,h);c.fills=solid(T.surface);c.cornerRadius=12;c.strokes=solid(T.border);c.strokeWeight=1;c.effects=shadowSm;c.clipsContent=true;if(parent)parent.appendChild(c);return c;}
function hbox(parent){const f=figma.createFrame();f.layoutMode='HORIZONTAL';f.fills=[];f.primaryAxisSizingMode='AUTO';f.counterAxisSizingMode='AUTO';if(parent)parent.appendChild(f);return f;}
function vbox(parent){const f=figma.createFrame();f.layoutMode='VERTICAL';f.fills=[];f.primaryAxisSizingMode='AUTO';f.counterAxisSizingMode='AUTO';if(parent)parent.appendChild(f);return f;}
function button(label,primary,parent){const b=hbox(parent);b.paddingLeft=20;b.paddingRight=20;b.paddingTop=11;b.paddingBottom=11;b.cornerRadius=8;b.counterAxisAlignItems='CENTER';b.primaryAxisAlignItems='CENTER';b.itemSpacing=8;b.fills=primary?solid(T.accent):solid(T.surface);if(!primary){b.strokes=solid(T.border);b.strokeWeight=1;}txt(label,14,'Semi Bold',primary?white:T.text,b);return b;}
function chip(label,color,parent){const p=hbox(parent);p.paddingLeft=12;p.paddingRight=12;p.paddingTop=6;p.paddingBottom=6;p.cornerRadius=999;p.fills=solid(tint(color,0.12));p.strokes=solid(tint(color,0.45));p.strokeWeight=1;p.counterAxisAlignItems='CENTER';txt(label,13,'Medium',color,p);return p;}
function kv(parent,y,w,label,value){place(txt(label,13,'Medium',T.textSub,parent),20,y);const v=txtW(value,13,'Semi Bold',T.text,parent,w-40);v.x=20;v.y=y;v.textAlignHorizontal='RIGHT';}
const NAV=['Dashboard','Input & Proses Analisis','Detail Ulasan','Rekomendasi Strategi','Ekspor Laporan','Tentang & Bantuan'];
function shell(name,x,active){
 const fr=figma.createFrame();fr.name=name;fr.resize(1440,1024);fr.x=x;fr.y=0;fr.fills=solid(T.bg);fr.layoutMode='VERTICAL';fr.itemSpacing=0;fr.clipsContent=true;fr.primaryAxisSizingMode='FIXED';fr.counterAxisSizingMode='FIXED';
 const nav=figma.createFrame();nav.name='Navbar';nav.resize(1440,64);nav.fills=solid(T.surface);nav.layoutMode='HORIZONTAL';nav.primaryAxisAlignItems='SPACE_BETWEEN';nav.counterAxisAlignItems='CENTER';nav.paddingLeft=32;nav.paddingRight=32;nav.primaryAxisSizingMode='FIXED';nav.counterAxisSizingMode='FIXED';nav.effects=shadowSm;fr.appendChild(nav);
 const brand=hbox(nav);brand.counterAxisAlignItems='CENTER';brand.itemSpacing=12;rrect(28,28,T.accent,6,brand);txt('Sentara — Analisis Ulasan E-Commerce',16,'Semi Bold',T.text,brand);
 const ui=hbox(nav);ui.counterAxisAlignItems='CENTER';ui.itemSpacing=12;txt('Aditya Rahmatullah',14,'Medium',T.textSub,ui);ell(36,tint(T.accent,0.25),ui);
 const body=figma.createFrame();body.name='Body';body.resize(1440,960);body.fills=[];body.layoutMode='HORIZONTAL';body.itemSpacing=0;body.primaryAxisSizingMode='FIXED';body.counterAxisSizingMode='FIXED';fr.appendChild(body);
 const side=figma.createFrame();side.name='Sidebar';side.resize(220,960);side.fills=solid(T.surface);side.layoutMode='VERTICAL';side.itemSpacing=4;side.paddingLeft=16;side.paddingRight=16;side.paddingTop=16;side.primaryAxisSizingMode='FIXED';side.counterAxisSizingMode='FIXED';side.effects=shadowSm;body.appendChild(side);
 for(const it of NAV){const ni=figma.createFrame();ni.name='NavItem';ni.resize(188,40);ni.layoutMode='HORIZONTAL';ni.counterAxisAlignItems='CENTER';ni.itemSpacing=12;ni.paddingLeft=14;ni.cornerRadius=8;ni.primaryAxisSizingMode='FIXED';ni.counterAxisSizingMode='FIXED';const a=it===active;ni.fills=a?solid(tint(T.accent,0.12)):[];rrect(8,8,a?T.accent:T.border,4,ni);txt(it,14,a?'Semi Bold':'Medium',a?T.accent:T.textSub,ni);side.appendChild(ni);}
 const main=figma.createFrame();main.name='MainContent';main.resize(1220,960);main.fills=[];main.clipsContent=true;body.appendChild(main);
 figma.currentPage.appendChild(fr);
 return {fr,main};
}
function head(main,title,sub){place(txt(title,20,'Bold',T.text,main),32,32);place(txtW(sub,14,'Medium',T.textSub,main,820),32,68);}
(function landing(){
 const fr=figma.createFrame();fr.name='00 - Akses Aplikasi (Streamlit)';fr.resize(1440,1024);fr.x=-1560;fr.y=0;fr.fills=solid(T.bg);fr.clipsContent=true;figma.currentPage.appendChild(fr);
 const ch=figma.createFrame();ch.name='BrowserBar';ch.resize(1440,48);ch.fills=solid(hex('#E9EBEE'));ch.layoutMode='HORIZONTAL';ch.counterAxisAlignItems='CENTER';ch.itemSpacing=16;ch.paddingLeft=20;ch.paddingRight=20;ch.primaryAxisSizingMode='FIXED';ch.counterAxisSizingMode='FIXED';fr.appendChild(ch);place(ch,0,0);
 const dots=hbox(ch);dots.itemSpacing=8;dots.counterAxisAlignItems='CENTER';ell(12,hex('#FF5F57'),dots);ell(12,hex('#FEBC2E'),dots);ell(12,hex('#28C840'),dots);
 const addr=figma.createFrame();addr.resize(960,30);addr.fills=solid(white);addr.cornerRadius=8;addr.layoutMode='HORIZONTAL';addr.counterAxisAlignItems='CENTER';addr.paddingLeft=14;addr.primaryAxisSizingMode='FIXED';addr.counterAxisSizingMode='FIXED';ch.appendChild(addr);txt('https://sentara.streamlit.app',13,'Regular',T.text,addr);
 const tg=figma.createFrame();tg.layoutMode='HORIZONTAL';tg.fills=solid(tint(T.pos,0.14));tg.cornerRadius=6;tg.paddingLeft=10;tg.paddingRight=10;tg.paddingTop=4;tg.paddingBottom=4;tg.counterAxisAlignItems='CENTER';tg.primaryAxisSizingMode='AUTO';tg.counterAxisSizingMode='AUTO';ch.appendChild(tg);txt('Running',12,'Medium',T.pos,tg);
 const hero=vbox(fr);hero.name='Hero';hero.counterAxisAlignItems='CENTER';hero.itemSpacing=20;hero.counterAxisSizingMode='FIXED';hero.resize(820,10);hero.primaryAxisSizingMode='AUTO';place(hero,310,180);
 const logo=figma.createFrame();logo.resize(76,76);logo.cornerRadius=20;logo.fills=solid(T.accent);logo.layoutMode='HORIZONTAL';logo.primaryAxisAlignItems='CENTER';logo.counterAxisAlignItems='CENTER';logo.primaryAxisSizingMode='FIXED';logo.counterAxisSizingMode='FIXED';hero.appendChild(logo);txt('S',36,'Bold',white,logo);
 txt('Sentara',46,'Bold',T.text,hero);
 const tl=txtW('Analisis Sentimen Ulasan Produk E-Commerce Berbasis IndoBERT',19,'Medium',T.textSub,hero,820);tl.textAlignHorizontal='CENTER';
 const ds=txtW('Masukkan ulasan produk toko Anda, lalu sistem mengklasifikasikan sentimen secara otomatis menjadi Positif, Negatif, atau Netral menggunakan model IndoBERT — dan memberikan rekomendasi strategi pemasaran berbasis data.',15,'Regular',T.textSub,hero,660);ds.textAlignHorizontal='CENTER';
 const chips=hbox(hero);chips.itemSpacing=12;chips.counterAxisAlignItems='CENTER';chips.paddingTop=4;chip('3 Kelas Sentimen',T.accent,chips);chip('Model IndoBERT',T.pos,chips);chip('Rekomendasi Otomatis',T.neu,chips);
 const bwrap=hbox(hero);bwrap.paddingTop=8;const b=button('Mulai Analisis  →',true,bwrap);b.paddingLeft=28;b.paddingRight=28;b.paddingTop=14;b.paddingBottom=14;
 chip('Status model: Siap digunakan',T.pos,hero);
 const ft=txtW('Skripsi · Aditya Rahmatullah (60900122038) · Program Studi Sistem Informasi',13,'Regular',T.textSub,fr,1440);ft.textAlignHorizontal='CENTER';place(ft,0,956);
})();
function buildExport(main){
 head(main,'Ekspor & Unduh Hasil Analisis','Unduh data ulasan berlabel, ringkasan, dan rekomendasi dalam berbagai format');
 const sb=card(1156,60,main);place(sb,32,108);sb.fills=solid(tint(T.pos,0.1));sb.strokes=solid(tint(T.pos,0.4));ell(10,T.pos,sb).x=24;sb.children[0].y=25;place(txt('Laporan analisis berhasil disiapkan — 1.024 ulasan terklasifikasi dengan Macro F1-Score 87,3%.',14,'Medium',T.pos,sb),46,20);
 const opts=[['Unduh Data (CSV)','Ulasan + label sentimen + skor keyakinan (.csv)','Unduh'],['Laporan Lengkap (PDF)','Ringkasan, grafik, dan rekomendasi strategi (.pdf)','Unduh'],['Grafik Visual (PNG)','Distribusi, tren sentimen, dan word cloud (.png)','Unduh'],['Salin Ringkasan','Ringkasan teks siap untuk laporan skripsi','Salin']];
 const xs=[32,325,618,911];
 opts.forEach((o,i)=>{const c=card(277,176,main);place(c,xs[i],196);rrect(40,40,tint(T.accent,0.16),10,c).x=20;c.children[0].y=20;place(txtW(o[0],15,'Semi Bold',T.text,c,237),20,72);place(txtW(o[1],13,'Regular',T.textSub,c,237),20,100);const b=button(o[2],i<3,c);place(b,20,128);});
 const ic=card(560,196,main);place(ic,32,396);place(txt('Sertakan dalam Ekspor',15,'Semi Bold',T.text,ic),20,20);const items=['Distribusi sentimen (donut)','Word cloud kata dominan','Tren sentimen 7 hari terakhir','Tabel detail ulasan + skor','Rekomendasi strategi pemasaran'];items.forEach((it,i)=>{const y=58+i*26;const bx=rrect(16,16,T.accent,4,ic);place(bx,24,y);place(txt('✓',11,'Bold',white,ic),27.5,y+1);place(txt(it,13,'Medium',T.text,ic),50,y);});
 const sc=card(564,196,main);place(sc,608,396);place(txt('Ringkasan yang Diekspor',15,'Semi Bold',T.text,sc),20,20);kv(sc,60,564,'Total ulasan dianalisis','1.024');kv(sc,86,564,'Positif / Netral / Negatif','54% / 28% / 18%');kv(sc,112,564,'Macro F1-Score model','87,3%');kv(sc,138,564,'Status reputasi toko','GOOD');kv(sc,164,564,'Jumlah rekomendasi','3 strategi');
 const act=hbox(main);act.itemSpacing=12;place(act,32,616);button('Selesai & Kembali ke Dashboard',true,act);button('Jadwalkan Analisis Berikutnya',false,act);
}
function buildAbout(main){
 head(main,'Tentang Aplikasi & Cara Pakai','Sentara — sistem analisis sentimen ulasan e-commerce berbasis IndoBERT');
 const ac=card(1156,150,main);place(ac,32,108);place(txt('Tentang Sentara',15,'Semi Bold',T.text,ac),20,20);place(txtW('Sentara adalah sistem analisis sentimen ulasan produk e-commerce berbasis IndoBERT (indolem/indobert-base-uncased) yang di-fine-tune untuk klasifikasi tiga kelas: Positif, Negatif, dan Netral. Model dilatih dari gabungan tiga dataset publik — SmSA (IndoNLU), PRDECT-ID, dan Review Product Shopee (Kaggle) — total 20.608 ulasan, lalu diuji pada ±1.000 ulasan OmorfoShop Official Store via Shopee Open Platform API. Tujuannya membantu pemilik toko memahami persepsi pelanggan dan menyusun strategi pemasaran berbasis data.',14,'Regular',T.textSub,ac,1100),20,52);
 const stc=card(1156,182,main);place(stc,32,278);place(txt('Cara Pakai dalam 5 Langkah',15,'Semi Bold',T.text,stc),20,20);
 const row=hbox(stc);row.itemSpacing=8;row.counterAxisAlignItems='CENTER';place(row,20,56);
 const steps=[['Hubungkan Toko','OAuth2 Shopee Open Platform'],['Ambil Ulasan','±1.000 ulasan produk toko'],['Jalankan IndoBERT','Klasifikasi 3 kelas sentimen'],['Lihat Hasil','Dashboard, detail & word cloud'],['Ekspor & Strategi','Unduh laporan + rekomendasi']];
 steps.forEach((s,i)=>{const col=vbox(row);col.counterAxisSizingMode='FIXED';col.resize(196,10);col.primaryAxisSizingMode='AUTO';col.counterAxisAlignItems='CENTER';col.itemSpacing=8;const circ=figma.createFrame();circ.resize(36,36);circ.cornerRadius=999;circ.fills=solid(T.accent);circ.layoutMode='HORIZONTAL';circ.primaryAxisAlignItems='CENTER';circ.counterAxisAlignItems='CENTER';circ.primaryAxisSizingMode='FIXED';circ.counterAxisSizingMode='FIXED';col.appendChild(circ);txt(String(i+1),16,'Bold',white,circ);const ti=txtW(s[0],14,'Semi Bold',T.text,col,196);ti.textAlignHorizontal='CENTER';const de=txtW(s[1],12,'Regular',T.textSub,col,196);de.textAlignHorizontal='CENTER';if(i<4){txt('→',18,'Regular',tint(T.text,0.4),row);}});
 const tc=card(560,176,main);place(tc,32,496);place(txt('Teknologi yang Digunakan',15,'Semi Bold',T.text,tc),20,20);const wrap=figma.createFrame();wrap.layoutMode='HORIZONTAL';wrap.layoutWrap='WRAP';wrap.fills=[];wrap.resize(520,10);wrap.primaryAxisSizingMode='FIXED';wrap.counterAxisSizingMode='AUTO';wrap.itemSpacing=8;wrap.counterAxisSpacing=8;tc.appendChild(wrap);place(wrap,20,52);['Python','HuggingFace Transformers','IndoBERT','Streamlit','Scikit-learn','Pandas','Plotly','WordCloud','Shopee Open API'].forEach(t=>chip(t,T.textSub,wrap));
 const inf=card(564,176,main);place(inf,608,496);place(txt('Informasi Skripsi',15,'Semi Bold',T.text,inf),20,20);kv(inf,58,564,'Nama','Aditya Rahmatullah');kv(inf,84,564,'NIM','60900122038');kv(inf,110,564,'Program Studi','Sistem Informasi');kv(inf,136,564,'Evaluasi utama / Capaian','Macro F1 87,3% (≥85%)');
}
const ex=shell('05 - Ekspor & Unduh Hasil',6240,'Ekspor Laporan');buildExport(ex.main);
const ab=shell('06 - Tentang & Cara Pakai',7800,'Tentang & Bantuan');buildAbout(ab.main);
figma.notify('3 layar alur ditambahkan');
return 'done';
})();
