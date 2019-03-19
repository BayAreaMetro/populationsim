#
# Check persons and households join without fails.
# Created when debugging model run core crashes as a stop-gap measure;
# TODO: figure out why this is needed at all
#
library(dplyr)
library(tidyr)

# TARGET_DIR     <- Sys.getenv("TARGET_DIR")  # The location of the input files
TARGET_DIR      <- "M:\\Application\\Model One\\RTP2021\\Scenarios\\2050_TM150_FU1_RT_00"

TARGET_DIR      <- gsub("\\\\","/",TARGET_DIR) # switch slashes around
PERSON_FILE     <- file.path(TARGET_DIR,"INPUT","popsyn","personFile.run16_RisingTides.2050.csv")
HOUSEHOLD_FILE  <- file.path(TARGET_DIR,"INPUT","popsyn","hhFile.run16_RisingTides.2050.csv")

PERSON_OUT_FILE     <- gsub(".csv","_new.csv", PERSON_FILE)
HOUSEHOLD_OUT_FILE  <- gsub(".csv","_new.csv", HOUSEHOLD_FILE)

person_data    <- read.table(file = PERSON_FILE,    header=TRUE, sep=",")
household_data <- read.table(file = HOUSEHOLD_FILE, header=TRUE, sep=",")

print(paste("Read",nrow(person_data),"from",PERSON_FILE))
print(paste("Read",nrow(household_data),"from",HOUSEHOLD_FILE))

ph_data     <- full_join(person_data, household_data)

# these have person data without households
missing_hh  <- ph_data[is.na(ph_data$hworkers),]
print(paste("Removing",nrow(missing_hh),"with missing household data"))
# these have household data without persons
missing_p   <- ph_data[is.na(ph_data$AGE),]
print(paste("Removing",nrow(missing_p),"with missing person data"))

remove_hh   <- unique(rbind(missing_hh["HHID"], missing_p["HHID"])) %>% mutate(to_remove=1)
print(paste("Removing",nrow(remove_hh),"households"))

person_data <- left_join(person_data, remove_hh) 
person_data <- subset(person_data, is.na(to_remove)) %>% select(-to_remove)
print(paste("Left with",nrow(person_data),"person rows"))

household_data <- left_join(household_data, remove_hh)
household_data <- subset(household_data, is.na(to_remove)) %>% select(-to_remove)
print(paste("Left with",nrow(household_data),"household rows"))

write.table(person_data,    PERSON_OUT_FILE,    sep=",", row.names=FALSE)
write.table(household_data, HOUSEHOLD_OUT_FILE, sep=",", row.names=FALSE)
