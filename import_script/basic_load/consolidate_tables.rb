#!/usr/bin/env ruby

# Script called by data_load to merge the various 
# individual tables describing events and diaries into 
# two coherent tables with primary keys. Needs to do
# a bit of munging to get event names right.
require 'bdb'
require 'mysql'
require 'logger'


def create_old_diary_event_names
  #Get rid of diary entries without an event id - they're antique test entries.
  @dbh.query("DELETE FROM `old_diary` WHERE `event_id`=''")
  @log.info("Deleted #{@dbh.affected_rows} old_diary entries without event_ids")
  @dbh.query("DELETE FROM `diary` WHERE `event_id`=''")
  @log.info("Deleted #{@dbh.affected_rows} diary entries without event_ids")
  @dbh.query("DELETE FROM `event_name` WHERE `event_id`=''")
  @log.info("Deleted #{@dbh.affected_rows} event names without event_ids")

  # Create entries in event_name table for any events that had their names
  # as their keys, and so didn't have an event_name entry.
  # WHERE clause is needed because some events with names as keys, *do* have
  # entries in event_name table. Honest.
  #
  # (Because of a bug in mysql (http://bugs.mysql.com/bug.php?id=10327)
  # it isn't possible to execute the next insert query straight into the
  # event_names table. Instead we have to create a temporary table to hold
  # the results, and then insert from there back into event_name. Bit silly,
  # really.)
  query_string="CREATE TEMPORARY TABLE new_event_names AS
                SELECT DISTINCT
                  old_diary.event_id, old_diary.event_id AS event_name
                FROM 
                  old_diary
                WHERE
                  !(old_diary.event_id = ANY(SELECT event_id FROM event_name)) AND !(old_diary.event_id = '')"
 @dbh.query(query_string)
 
# and now we insert that into event_names:
 query_string = "INSERT INTO event_name 
                SELECT * FROM new_event_names"
 @dbh.query(query_string)


  @log.info("#{@dbh.affected_rows} event names created")
end

def merge_tables_diary
  @log.info "Merging diary"
# Merge all the date tables together, make the event_id the primary key in the generated table
#  merge_query = "CREATE TABLE diary_merged (`datetime` DATETIME NOT NULL ) 
  merge_query = "CREATE TABLE diary_merged (`datetime` DATETIME NOT NULL, PRIMARY KEY(`datetime`)) 
  SELECT
  diary.datetime_actual as datetime, diary.event_id,booked_by.name as booked_by,confirmed.confirmed, cancelled.cancelled, discounted.discounted,outside_hire.outside_hire,private_event.private_event
  FROM diary
  LEFT JOIN booked_by ON diary.datetime = booked_by.datetime
  LEFT JOIN confirmed ON diary.datetime = confirmed.datetime
  LEFT JOIN cancelled ON diary.datetime = cancelled.datetime
  LEFT JOIN discounted ON diary.datetime = discounted.datetime
  LEFT JOIN outside_hire ON diary.datetime = outside_hire.datetime
  LEFT JOIN private_event ON diary.datetime = private_event.datetime"

  @dbh.query(merge_query)

end


def merge_tables_old_diary
  @log.info "Merging old diary"
  merge_query = "INSERT INTO diary_merged SELECT
                  old_diary.datetime_actual, old_diary.event_id,booked_by.name as booked_by,confirmed.confirmed, cancelled.cancelled, discounted.discounted,outside_hire.outside_hire,private_event.private_event
                  FROM old_diary
                  LEFT JOIN booked_by ON old_diary.datetime = booked_by.datetime
                  LEFT JOIN confirmed ON old_diary.datetime = confirmed.datetime
                  LEFT JOIN cancelled ON old_diary.datetime = cancelled.datetime
                  LEFT JOIN discounted ON old_diary.datetime = discounted.datetime
                  LEFT JOIN outside_hire ON old_diary.datetime = outside_hire.datetime
                  LEFT JOIN private_event ON old_diary.datetime = private_event.datetime"

  @dbh.query(merge_query)
end


def merge_tables_events
  @log.info "Merging events"
  # Merge all the event things together, make the event_id the primary key in the generated table
  merge_query ="CREATE TABLE events_merged (`event_id` VARCHAR(128) NOT NULL, PRIMARY KEY(`event_id`)) 
                SELECT
                event_name.event_id,event_name.event_name,copy.copy,copy_summary.copy_summary,duration.duration,image_credits.image_credits,terms.terms
                FROM
                `event_name`
                LEFT JOIN copy ON event_name.event_id = copy.event_id
                LEFT JOIN copy_summary ON event_name.event_id = copy_summary.event_id
                LEFT JOIN duration ON event_name.event_id = duration.event_id
                LEFT JOIN image_credits ON event_name.event_id = image_credits.event_id
                LEFT JOIN terms ON event_name.event_id = terms.event_id"
  @dbh.query(merge_query)
end

def rename_tables
  @log.info "Dropping temporary diary table"
  @dbh.query("DROP TABLE diary")
  @log.info "Renaming diary_merged and events_merged"
  @dbh.query("RENAME TABLE events_merged TO events")
  @dbh.query("RENAME TABLE diary_merged TO diary")

  @log.info "Adding foreign key constraints to tables"
  @dbh.query("ALTER TABLE diary ADD CONSTRAINT FK_diary_events FOREIGN KEY (event_id) REFERENCES events(event_id)")
#  @dbh.query("ALTER TABLE roles_merged ADD CONSTRAINT FK_roles_events FOREIGN KEY (event_id) REFERENCES events(event_id)")
  @dbh.query("ALTER TABLE notes ADD CONSTRAINT FK_notes_members FOREIGN KEY (member_id) REFERENCES members(member_id)")
  @dbh.query("ALTER TABLE vol_roles_merged ADD CONSTRAINT FK_roles_members FOREIGN KEY (member_id) REFERENCES members(member_id)")

end

