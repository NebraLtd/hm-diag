while :
do
    gunicorn --bind 0.0.0.0:5000 --timeout 300 hw_diag:wsgi_app
    sleep 5
done
