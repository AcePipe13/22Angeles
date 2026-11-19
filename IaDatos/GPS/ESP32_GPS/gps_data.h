#ifndef GPS_DATA_H
#define GPS_DATA_H

struct GPSData {
  double lat;
  double lon;
  double alt;
  double speed;
  double accuracy;
  double heading;

  unsigned long packet;

  bool valid;
};

#endif