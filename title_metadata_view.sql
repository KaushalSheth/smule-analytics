drop view title_metadata_vw;
create view title_metadata_vw as
select  tm.fixed_title,
        tm.rating_nbr,
        tm.artist,
        tm.singer_type,
        fs.perf_cnt,
        adj_weighted_cnt
from    title_metadata tm
        inner join favorite_song fs on fs.fixed_title = tm.fixed_title
order by fs.perf_cnt desc;

CREATE OR REPLACE FUNCTION title_metadata_vw_update()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $function$
   BEGIN
       UPDATE title_metadata SET rating_nbr=NEW.rating_nbr, singer_type=NEW.singer_type WHERE fixed_title=OLD.fixed_title;
       RETURN NEW;
    END;
$function$;

CREATE TRIGGER title_metadata_vw_update_trg
    INSTEAD OF UPDATE ON
      title_metadata_vw FOR EACH ROW EXECUTE PROCEDURE title_metadata_vw_update();
