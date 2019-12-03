#!/bin/bash
if [ -z "$1" ]
then 
    echo "call by choosing a csv to parse"
    exit
fi

rm -f csvsession.pickle
python ../csv_analyzer/csv_analyzer.py t x y offx offy v -f $1 -x t --sessionstart --terminate --colorbyplot
python ../csv_analyzer/csv_analyzer.py v -f $1 -x t --title "Mouse Speed" --sessioncontinue --colorbyplot &
python ../csv_analyzer/csv_analyzer.py v x -f $1 -x t --hideplot1 --filter "SELECT x WHERE v > 150" --filtertitle "x when v > 150" --sessioncontinue --colorbyplot &
sleep 1
python ../csv_analyzer/csv_analyzer.py x y offx offy --scatter -f $1 --title "Path Tracking" --sessioncontinue --colorbyplot &

trap killplots SIGINT

killplots()
{
    for pid in $(ps -ef | awk '/python ..\57csv_analyzer\57csv_analyzer.py/ {print $2}'); do kill -9 $pid; done
    exit 0
}

while :
do
    sleep 1
done
