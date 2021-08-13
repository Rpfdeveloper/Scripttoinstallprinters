#!/bin/bash

echo Seleccione marca de la impresora a instalar: 1-Konica 2-Sharp 3-Toshiba.
read marca
if [ $marca -eq 1 ]; then

	echo Introduzca modelo:  1-bizhub C250i  2-bizhub C280  3-bizhub C750i.
	read modelok
		case $modelok in
			3)
			wget https://dl.konicaminolta.eu/es?tx_kmanacondaimport_downloadproxy[fileId]=10f13fbba3d408cdb703943fde49abdb&tx_kmanacondaimport_downloadproxy[documentId]=128230&tx_kmanacondaimport_downloadproxy[system]=KonicaMinolta&tx_kmanacondaimport_downloadproxy[language]=ES&type=1558521685;;
			2)
			wget https://dl.konicaminolta.eu/es?tx_kmanacondaimport_downloadproxy[fileId]=10f13fbba3d408cdb703943fde49abdb&tx_kmanacondaimport_downloadproxy[documentId]=128230&tx_kmanacondaimport_downloadproxy[system]=KonicaMinolta&tx_kmanacondaimport_downloadproxy[language]=ES&type=1558521685;;
			1)
			wget ;;
			*)
			echo modelo erroneo.;;
			
		esac
elif [ $marca -eq 2 ]; then

	echo Introduzca modelo:  1-MX3061  2-MXC304W  3-MX3070V.
	read modelos
		case $modelos in
			3)
			#conexion a página de sharp, extracción .tar, eliminado archivo, reuvicacion de archivo.ppd a servidor cups, instalacion impresora y borrado archivos extraidos 
			
			wget https://www.sharp.es/cps/rde/xbcr/documents/documents/Service_Information/Drivers/sharp-1.1-mx-c55-ps.tar

			tar -xvf sharp-1.1-mx-c55-ps.tar

			rm -r sharp-1.1-mx-c55-ps.tar 

			mv sharp-1.1-mx-c55-ps/Sharp-MX-4071-ps.ppd /usr/share/cups/model 
			
			echo introduzca ip de la impresora

			read ip

			/usr/sbin/lpadmin -p "SharpMX3070V" -E -v lpd://$ip -P "/usr/share/cups/model/Sharp-MX-4071-ps.ppd" 
			
			rm -r sharp-1.1-mx-c55-ps

			;;
			2)
			wget https://www.sharp.es/cps/rde/xbcr/documents/documents/Service_Information/Drivers/sharp-1.1-mx-c55-ps.tar;;
			1)
			wget  https://www.sharp.es/cps/rde/xbcr/documents/documents/Service_Information/Drivers/sharp-1.6-mx-c52-ps.tar;;  

		esac
elif [ $marca -eq 3 ]; then

	echo Introduzca modelo:  1-MX3061  2-MXC304W  3-e-studio263cs.
	read modelos
		case $modelos in
			3)
			#conexion a página de toshiba, extracción .tar, eliminado archivo, reuvicacion de archivo.ppd a servidor cups, instalacion impresora y borrado archivos extraidos 
			
			wget https://toshibatec.eu/publicsite-service/resource/download/pseu/en/7eab80d2-43fd-4415-99e1-807065531500/932b7a3584aa90664edbe9c4f3cd6946/TO263S_a.ppd.gz

			gzip -d TO263S_a.ppd.gz  

			mv TO263S_a.ppd /usr/share/cups/model 
			
			echo introduzca ip de la impresora

			read ip

			/usr/sbin/lpadmin -p "e-studio263c" -E -v lpd://$ip -P "/usr/share/cups/model/TO263S_a.ppd" 
			
		

			;;
			2)
			wget https://www.sharp.es/cps/rde/xbcr/documents/documents/Service_Information/Drivers/sharp-1.1-mx-c55-ps.tar;;
			1)
			wget  https://www.sharp.es/cps/rde/xbcr/documents/documents/Service_Information/Drivers/sharp-1.6-mx-c52-ps.tar;;  

		esac

else 

echo marca fuera de rango

fi
