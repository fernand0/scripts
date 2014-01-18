#!/bin/sh

host=$1
name=$2
geom=$3

if [ "$name" = "" ] 
then
	name=$1
fi

if [ "$geom" = "" ] 
then
	geom="+300+421"
fi


gnome-terminal --title $name --geometry $geom --execute ssh -X $host  &
