PID=603451
while kill -0 $PID 2>/dev/null; do
	echo "Checking process $PID"   
    sleep 60
done
echo "Process $PID has finished"   
