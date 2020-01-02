#!/bin/bash
if [ -z "$1" ]
then 
    echo "call by choosing a csv to parse. Create one using generate_path_data.py"
    exit
fi

rm -f csvsession.pickle
python ../csv_analyzer/csv_analyzer.py t x y offx offy v -f $1 -x t --sessionstart --terminate --colorbyplot
python ../csv_analyzer/csv_analyzer.py t v --title "Mouse Speed" --sessioncontinue --colorbyplot &
python ../csv_analyzer/csv_analyzer.py t v x -x t --filter "SELECT x WHERE v > 150" --sessioncontinue --colorbyplot --title "x WHERE v > 150" &
python ../csv_analyzer/csv_analyzer.py t v x -x t --filter "SELECT x WHERE t > 1.5" --sessioncontinue --colorbyplot --title "x WHERE t > 1.5" &
python ../csv_analyzer/csv_analyzer.py t v x --filter "numpy.where(numpy.array(dict_data[\"t\"]) > 1.50)" --sessioncontinue --colorbyplot --title "numpy.where(numpy.array(dict_data[\"t\"]) > 1.50)" &
python ../csv_analyzer/csv_analyzer.py t v x -x t --filter "SELECT x WHERE t > 1.5 AND v > 150" --sessioncontinue --colorbyplot --title "x WHERE t > 1.5 AND v > 150" &
sleep 1
python ../csv_analyzer/csv_analyzer.py x y --scatter --title "Path Tracking" --sessioncontinue --colorbyplot &
python ../csv_analyzer/csv_analyzer.py x y offx offy --scatter --title "Path Tracking Compare" --sessioncontinue --colorbyplot &

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
