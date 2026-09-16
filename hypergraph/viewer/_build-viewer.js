const fs = require('fs');
const path = require('path');

const graph = JSON.parse(fs.readFileSync(
  path.resolve(__dirname, '..', 'KB', 'graph', 'hypergraph.json'), 'utf-8'
));

const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<title>KB Hypergraph Viewer</title>
<script src="vis-network.min.js"><\/script>
<style>
html, body { margin:0; padding:0; width:100%; height:100%; overflow:hidden; background:#0d1117; color:#c9d1d9; font-family:'Segoe UI',sans-serif; }
#toolbar { height:44px; background:#161b22; border-bottom:1px solid #30363d; display:flex; align-items:center; padding:0 16px; gap:12px; font-size:12px; }
#toolbar h1 { font-size:15px; font-weight:600; margin-right:8px; }
#toolbar select, #toolbar input { background:#0d1117; color:#c9d1d9; border:1px solid #30363d; border-radius:4px; padding:4px 8px; font-size:12px; }
#toolbar button { background:#21262d; color:#c9d1d9; border:1px solid #30363d; border-radius:4px; padding:4px 12px; font-size:12px; cursor:pointer; }
#toolbar button:hover { background:#30363d; }
#toolbar button.on { background:#1f6feb; border-color:#1f6feb; color:#fff; }
#toolbar .stats { margin-left:auto; font-size:11px; color:#8b949e; }
#graph { width:100%; height:calc(100vh - 44px); }
#legend { position:fixed; bottom:10px; left:10px; background:#161b22; border:1px solid #30363d; border-radius:6px; padding:10px 14px; font-size:11px; z-index:10; }
#legend div { display:flex; align-items:center; gap:6px; margin-bottom:3px; }
.dot { width:8px; height:8px; border-radius:50%; display:inline-block; }
.line { width:20px; height:2px; display:inline-block; }
#detail { display:none; position:fixed; top:50px; right:10px; width:340px; max-height:70vh; overflow-y:auto; background:#161b22; border:1px solid #30363d; border-radius:8px; padding:14px; font-size:12px; z-index:10; box-shadow:0 4px 20px rgba(0,0,0,0.5); }
#detail.show { display:block; }
#detail h3 { font-size:14px; margin-bottom:8px; color:#f0f6fc; }
#detail .x { position:absolute; top:8px; right:10px; cursor:pointer; color:#8b949e; font-size:16px; }
#detail .x:hover { color:#f0f6fc; }
#detail table { width:100%; border-collapse:collapse; }
#detail td { padding:3px 6px; border-bottom:1px solid #21262d; vertical-align:top; }
#detail td:first-child { color:#8b949e; width:80px; }
.conn { padding:4px 0; border-bottom:1px solid #21262d; font-size:11px; }
.etype { color:#d2a8ff; font-weight:600; }
</style>
</head>
<body>
<div id="toolbar">
  <h1>KB Hypergraph</h1>
  <select id="ft" onchange="draw()"><option value="all">All Nodes</option><option value="domain">Domains</option><option value="feature">Features</option><option value="domain,feature">Domains+Features</option><option value="shared_deps">Shared Dependencies (Hub)</option></select>
  <select id="fe" onchange="draw()"><option value="all">All Edges</option><option value="belongs_to_domain">belongs_to_domain</option><option value="has_artifact">has_artifact</option><option value="derived_from">derived_from</option><option value="references">references</option><option value="shares_dependency">shares_dependency</option></select>
  <input id="q" placeholder="Search..." oninput="draw()" style="width:140px"/>
  <button id="pb" class="on" onclick="tp()">Physics</button>
  <button onclick="rs()">Reset</button>
  <span class="stats" id="stats"></span>
</div>
<div id="graph"></div>
<div id="legend">
  <div><span class="dot" style="background:#f0883e"></span> Domain</div>
  <div><span class="dot" style="background:#58a6ff"></span> Feature</div>
  <div><span class="dot" style="background:#56d364"></span> Artifact</div>
  <div><span class="line" style="background:#8b949e"></span> belongs_to / has_artifact</div>
  <div><span class="line" style="background:#d2a8ff"></span> derived_from / references</div>
  <div><span class="line" style="background:#f0883e"></span> shares_dependency</div>
  <div><span class="dot" style="background:#f0883e;border-radius:2px"></span> Shared Dependency Hub</div>
</div>
<div id="detail"><span class="x" onclick="document.getElementById('detail').classList.remove('show')">&times;</span><h3 id="dt"></h3><table id="dp"></table><div id="dc"></div></div>
<script>
var D=${JSON.stringify(graph)};

var net,ph=true;
var NC={domain:{bg:'#f0883e',bd:'#d97706',fn:'#fff',sh:'diamond',sz:30},feature:{bg:'#1f6feb',bd:'#58a6ff',fn:'#fff',sh:'dot',sz:22},artifact:{bg:'#238636',bd:'#56d364',fn:'#c9d1d9',sh:'dot',sz:12},hub:{bg:'#cca700',bd:'#e6be00',fn:'#000',sh:'hexagon',sz:26}};
var EC={belongs_to_domain:'#8b949e',has_artifact:'#8b949e',derived_from:'#d2a8ff',references:'#d2a8ff',validates:'#d2a8ff',shares_dependency:'#f0883e'};

document.getElementById('stats').textContent=D.nodes.length+' nodes | '+D.edges.length+' edges | '+(D.hyperedges||[]).length+' hyperedges';
draw();

function draw(){
  var tf=document.getElementById('ft').value;
  var ef=document.getElementById('fe').value;
  var q=(document.getElementById('q').value||'').toLowerCase();

  // Special hub view for shared dependencies
  if(tf==='shared_deps'){return drawHubView(q);}

  var ns=D.nodes.slice();
  if(tf!=='all'){var ts=tf.split(',');ns=ns.filter(function(n){return ts.indexOf(n.type)>=0;});}
  if(q){
    var am={};
    if(D.alias_index){for(var a in D.alias_index){if(a.indexOf(q)>=0)(D.alias_index[a].nodes||[]).forEach(function(id){am[id]=1;});}}
    ns=ns.filter(function(n){return(n.label||'').toLowerCase().indexOf(q)>=0||n.id.toLowerCase().indexOf(q)>=0||am[n.id];});
  }
  var ids={};ns.forEach(function(n){ids[n.id]=1;});
  var es=D.edges.filter(function(e){return ids[e.source]&&ids[e.target];});
  if(ef!=='all')es=es.filter(function(e){return e.type===ef;});

  var vn=ns.map(function(n){
    var c=NC[n.type]||NC.artifact;
    return{id:n.id,label:n.label||n.id,color:{background:c.bg,border:c.bd,highlight:{background:c.bg,border:'#fff'}},font:{color:c.fn,size:n.type==='artifact'?9:12},shape:c.sh,size:c.sz};
  });
  var ve=es.map(function(e,i){
    var lbl=e.type;if(e.properties&&e.properties.pattern_label)lbl=e.properties.pattern_label;
    return{id:e.id||'e'+i,from:e.source,to:e.target,color:{color:EC[e.type]||'#484f58',opacity:0.6},arrows:{to:{enabled:true,scaleFactor:0.5}},title:lbl,dashes:e.type==='has_artifact'?[4,4]:false};
  });

  render(vn,ve,false);
}

function drawHubView(q){
  var vn=[];
  var ve=[];
  var featureIds={};

  // Get shared dependency hyperedges
  var sharedHyperedges=(D.hyperedges||[]).filter(function(h){
    return h.type==='cross_repo_pattern';
  });

  // Collect all feature nodes involved
  sharedHyperedges.forEach(function(h){
    (h.node_ids||[]).forEach(function(nid){featureIds[nid]=1;});
  });

  // Add feature nodes
  D.nodes.forEach(function(n){
    if(n.type==='feature'&&featureIds[n.id]){
      if(q&&(n.label||'').toLowerCase().indexOf(q)<0&&n.id.toLowerCase().indexOf(q)<0)return;
      var c=NC.feature;
      vn.push({id:n.id,label:n.label||n.id,level:1,color:{background:c.bg,border:c.bd,highlight:{background:c.bg,border:'#fff'}},font:{color:c.fn,size:13},shape:c.sh,size:c.sz});
    }
  });

  // Add hub nodes + spoke edges for each shared pattern
  sharedHyperedges.forEach(function(h,idx){
    var hubId='hub_'+idx;
    var label=h.label||'Shared Pattern';
    if(q&&label.toLowerCase().indexOf(q)<0)return;
    var repos=(h.properties&&h.properties.repos)||[];
    var evidence=h.properties&&h.properties.evidence||{};
    var conf=(h.properties&&h.properties.confidence)||'';

    // Hub node — fixed at level 0 (top row)
    var c=NC.hub;
    vn.push({
      id:hubId,
      label:label,
      level:0,
      color:{background:c.bg,border:c.bd,highlight:{background:c.bg,border:'#fff'}},
      font:{color:c.fn,size:11,multi:'html'},
      shape:c.sh,
      size:c.sz,
      title:label+'\\nRepos: '+repos.join(', ')+'\\nConfidence: '+conf
    });

    // Spoke edges from hub to each feature
    (h.node_ids||[]).forEach(function(nid,j){
      // Find the repo name for this feature to show what it uses
      var repo='';var evLabel='';
      D.nodes.forEach(function(n){if(n.id===nid&&n.properties)repo=n.properties.repo_name||'';});
      if(repo&&evidence[repo])evLabel=evidence[repo];

      ve.push({
        id:'hub_edge_'+idx+'_'+j,
        from:hubId,
        to:nid,
        color:{color:'#f0883e',opacity:0.8},
        arrows:{to:{enabled:true,scaleFactor:0.6}},
        title:evLabel||label,
        label:evLabel||'',
        font:{color:'#8b949e',size:9,strokeWidth:0},
        width:2
      });
    });
  });

  render(vn,ve,true);
}

function render(vn,ve,useHierarchy){
  var c=document.getElementById('graph');
  if(net){net.destroy();net=null;}
  var opts={
    interaction:{hover:true,tooltipDelay:200},
    edges:{smooth:{type:'continuous'},width:1.2}
  };
  if(useHierarchy){
    opts.layout={hierarchical:{direction:'UD',sortMethod:'directed',levelSeparation:150,nodeSpacing:180,blockShifting:true,edgeMinimization:true}};
    opts.physics={enabled:false};
  }else{
    opts.layout={improvedLayout:true};
    opts.physics={enabled:ph,solver:'forceAtlas2Based',forceAtlas2Based:{gravitationalConstant:-60,centralGravity:0.015,springLength:150,springConstant:0.03,damping:0.4},stabilization:{iterations:150}};
  }
  net=new vis.Network(c,{nodes:new vis.DataSet(vn),edges:new vis.DataSet(ve)},opts);
  net.once('stabilizationIterationsDone',function(){net.fit();});
  setTimeout(function(){if(net)net.fit();},2500);
  net.on('click',function(p){if(p.nodes.length>0)info(p.nodes[0]);else document.getElementById('detail').classList.remove('show');});
}

function info(id){
  var n;for(var i=0;i<D.nodes.length;i++)if(D.nodes[i].id===id){n=D.nodes[i];break;}
  if(!n)return;
  document.getElementById('dt').textContent=n.label||n.id;
  var h='<tr><td>Type</td><td>'+n.type+'</td></tr><tr><td>ID</td><td style="word-break:break-all;font-size:10px">'+n.id+'</td></tr>';
  if(n.properties)for(var k in n.properties){var v=n.properties[k];if(v!=null&&v!=='')h+='<tr><td>'+esc(k)+'</td><td>'+(typeof v==='object'?'<pre style="margin:0;font-size:10px;white-space:pre-wrap">'+JSON.stringify(v,null,1)+'</pre>':esc(String(v)))+'</td></tr>';}
  document.getElementById('dp').innerHTML=h;
  var ce=D.edges.filter(function(e){return e.source===id||e.target===id;});
  var ch='<div style="font-weight:600;margin:8px 0 4px;color:#8b949e">Connections ('+ce.length+')</div>';
  ce.forEach(function(e){var oid=e.source===id?e.target:e.source;var on;for(var j=0;j<D.nodes.length;j++)if(D.nodes[j].id===oid){on=D.nodes[j];break;}var ol=on?(on.label||on.id):oid;var dir=e.source===id?' \\u2192 ':' \\u2190 ';var reason='';if(e.properties&&e.properties.pattern_label)reason=' <span style="color:#f0883e;font-size:10px">['+esc(e.properties.pattern_label)+']</span>';if(e.properties&&e.properties.evidence_src)reason+=' <span style="color:#8b949e;font-size:10px">('+esc(e.properties.evidence_src)+' \\u2194 '+esc(e.properties.evidence_tgt||'')+')</span>';ch+='<div class="conn"><span class="etype">'+e.type+'</span>'+dir+esc(ol)+reason+'</div>';});
  document.getElementById('dc').innerHTML=ch;
  document.getElementById('detail').classList.add('show');
}

function tp(){ph=!ph;document.getElementById('pb').classList.toggle('on',ph);if(net)net.setOptions({physics:{enabled:ph}});}
function rs(){document.getElementById('ft').value='all';document.getElementById('fe').value='all';document.getElementById('q').value='';draw();}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
<\/script>
</body>
</html>`;

const outPath = path.resolve(__dirname, 'hypergraph-viewer.html');
fs.writeFileSync(outPath, html);
console.log('Written:', outPath, '(' + (html.length / 1024).toFixed(0) + 'KB)');
