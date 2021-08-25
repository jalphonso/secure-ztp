# Secure ZTP for Junos

## Installation

Update server ip and port in **ztp.env**. IP should be the docker host. Port should be the exposed port of the web service. (see "Change ZTP https port" section)

Update exposed port in docker-compose.yml (see "Change ZTP https port" section)

Update server tls certs in **nginx/certs/**

<div style="page-break-after: always"></div>

## DHCP Server
If using external dhcp server install required option 43 parameters and suboptions.

```
option space JNPR;
option JNPR.image-file-name code 0 = text;
option JNPR.config-file-name code 1 = text;
option JNPR.image-file-type code 2 = text;
option JNPR.transfer-mode code 3 = text;
option JNPR.alt-image-file-name code 4 =text;
option JNPR.http-port code 5 = text;
option JNPR.ftp-timeout code 7 = text;
option JNPR-encapsulation code 43 = encapsulate JNPR;
option option-150 code 150 = ip-address;

# Empty scope needed for local interface for daemon to start
subnet 172.31.50.64 netmask 255.255.255.192 {
}

subnet 172.31.25.0 netmask 255.255.255.0 {
  include "/etc/dhcp/ztp_hosts.conf";
  default-lease-time 21600;
  max-lease-time 43200;
  option JNPR.transfer-mode "https";
  option JNPR.http-port "8443";
  option JNPR.config-file-name "ztp.sh";
  option option-150 172.31.25.10;
  option subnet-mask 255.255.255.0;
  option routers 172.31.25.1;
}
```

Update host reservations
```
[root@jnpr-ztp ztp]# more /etc/dhcp/ztp_hosts.conf
host switch1 {
  option host-name "switch1";
  hardware ethernet d8:a7:d0:1a:3d:02;
  fixed-address 172.31.25.5;
}
```

**Note: You should also have a reachable NTP server and supply it as a dhcp option so the device undergoing ztp has the correct time. The time needs to be correct or cert validation might not succeed when validating the junos image during a ztp software upgrade/downgrade.**
<div style="page-break-after: always"></div>

## Adding ZTP hosts

add json files to the folder **ztp_jsons** following the example entry format.

you can name the files however you'd like as long as the extension is json. i.e. site1.json

Please note, site IP addresses must not be overlapping. Otherwise the last one in wins. The app must be restarted after any changes to any of the jsons files.

## Adding ZTP software and device configs

place the files in their respective directories **ztp_configs** and **ztp_software**.
<div style="page-break-after: always"></div>

## Docker Compose

### Building the app

```
docker-compose build
```

### Starting the app

```
docker-compose up -d
```

### Restarting the app

```
docker-compose restart
```

### Stopping the app

```
docker-compose down
```

### Container Logs

You can monitor the logs with the following command

```
docker-compose logs -f
```

or the last 100 lines for example

```
docker-compose logs -f --tail=100
```
<div style="page-break-after: always"></div>

## Change ZTP https port

First make sure the dhcp server sets the following option to the desired port. For isc-dhcp it looks like this
```
option JNPR.http-port "8443";
```

Second, update ztp.env
```
ZTP_PORT=8443
```

Third, update the docker-compose.yml exposed port mapping for the web service (left side of the colon only)
```
    ports:
      - "8443:443"
```

**Note: All three values need to match.**