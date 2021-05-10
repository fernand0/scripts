#!/bin/sh

if [ $# -eq 0 ]
then
	echo "You must provide a file name"
	exit
fi

while IFS=, read -r f1 f2 f3 f4 f5 f6 f7 f8 ; 
do   
	echo "Creating pass entry for $f1 $f2"; 
	echo "$f4" | pass insert -e "$f1/$f2" 
	sleep 1


done < "$1"
