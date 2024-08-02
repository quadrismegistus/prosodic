# Prosodic deployment instructions

1. Ensure you have Nginx installed on your server.

2. Copy the `nginx.conf` file to `/etc/nginx/sites-available/prosodic`
    * Note: Make sure to update the `server_name` and SSL certificate paths in the Nginx configuration file before deploying.

3. Create a symbolic link: `sudo ln -s /etc/nginx/sites-available/prosodic /etc/nginx/sites-enabled/`

4. Restart Nginx: `sudo systemctl restart nginx`

5. Install Supervisor: `sudo apt-get install supervisor`

6. Copy the Supervisor configuration: `sudo cp deployment/supervisor.conf /etc/supervisor/conf.d/prosodic.conf`
    * Note: Make sure to update the paths in the `supervisor.conf` file to match your project's location and user.

7. Create log directory: `sudo mkdir -p /var/log/prosodic`

8. Update Supervisor: 
   ```
   sudo supervisorctl reread
   sudo supervisorctl update
   ```

9. Start the Prosodic service: `sudo supervisorctl start prosodic`
