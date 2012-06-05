USE toolkit;
ALTER TABLE diary ADD CONSTRAINT FK_diary_events FOREIGN KEY (event_id) REFERENCES events(event_id);
ALTER TABLE roles_merged ADD CONSTRAINT FK_roles_events FOREIGN KEY (event_id) REFERENCES events(event_id);

ALTER TABLE notes ADD CONSTRAINT FK_notes_members FOREIGN KEY (member_id) REFERENCES members(member_id);
ALTER TABLE vol_roles_merged ADD CONSTRAINT FK_roles_members FOREIGN KEY (member_id) REFERENCES members(member_id);

