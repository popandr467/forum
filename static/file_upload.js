var cfid=0;
const flList=[];

(d=>{//обработчик добавления и удаления файлов
	const fu=d.getElementById('fileInput'),cp=d.getElementById('fcpct');
	if(!fu)return;
	d.getElementById('addFileBtn').addEventListener('click',e=>{e.preventDefault();fu.click();});
	fu.addEventListener('change',()=>{//когда выбрали файл
		const file=fu.files[0],cl=fu.cloneNode(true);
		fu.value='';
		if(!file)return;
		if(file.size<=(15<<20)){
			const dbt=d.createElement('button'),br=d.createElement('br'),sp=d.createElement('span'),dv=d.createElement('div');
			cl.style='';cl.disabled='true';
			dbt.textContent='Удалить';
			dbt.id='deleteBtn'
			dbt.addEventListener('click',e=>{//обработчик нажатия кнопки удаления
				(id=>{//удалить номер файла из списка
					const idx=flList.indexOf(id);
					if(idx>-1)flList.splice(idx,1);
				})(parseInt(e.target.previousElementSibling.id.match(/\d+/)[0]));
				e.target.parentElement.parentElement.remove();
			});
			cl.id='file'+(++cfid);
			sp.className='file';
			sp.appendChild(cl);
			sp.appendChild(dbt);
			sp.appendChild(br);
			dv.className='filecont';
			dv.appendChild(sp)
			cp.appendChild(dv);
			(id=>{if(!flList.includes(id))flList.push(id);})(cfid);
		}else{
			const err=d.createElement('div');
			err.className='err';
			err.innerText='Размер файла превышает 15 МБ';
			cp.appendChild(err);
			setTimeout(()=>{err.remove();},5000);
		}
	});
	//console.log(d.querySelector("form#myForm"));
	d.querySelector("form#myForm").addEventListener('submit',e=>{//при отправке данных
		e.preventDefault();
		//window.open('chrome://newtab');
		const lt=[];
		const l=[],fm=d.getElementById('fileContent'),tt=d.getElementById('ttl'),tx=d.getElementById('txt'),fl=d.getElementById('flist');
		const l2=[];
		function addInput(nm,vl){//добавление нового поля
			const inp=d.createElement('input');
			inp.type='hidden';
			inp.name=nm;
			inp.value=vl;
			fm.appendChild(inp);//добавляем все данные в скрытую форму
			//lt.push({name:nm,value:vl});
		};
		function sendfile(ab,nm) {
			const fd=new FormData();
			fd.append('file',new Blob([ab]));
			fd.append('name',nm);
			return fetch('/filerx/',{method:'POST',body:fd}).then(rp=>rp.text());
		};
		for(let i of flList){
			if(i){
				let flinp=d.querySelector('input#file'+i);
				l.push(flinp.files[0].arrayBuffer().then(ct=>{l2.push(sendfile(ct,flinp.files[0].name));}));
			}
		}
		if(tt)addInput('title',tt.value);
		if(tx)addInput('content',tx.value);
		addInput('flist',flList.join(','));
		//console.log(d.getElementById('flist').value.split(","));
		Promise.all(l).then(res=>{
			Promise.all(l2).then(res2=>{
				addInput('fids',res2.join(','));
				fm.submit();
			});
		});
	});
})(document);//макс. число аргументов у функции - 125357