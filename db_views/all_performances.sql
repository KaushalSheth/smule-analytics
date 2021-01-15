CREATE OR REPLACE VIEW all_performances AS
SELECT  p.*,
        split_part(p.key::text, '_'::text, 1) AS instance_key,
        COALESCE(s.performed_by, p.owner_handle) AS partner_name,
        COALESCE(s.pic_url, p.owner_pic_url) AS partner_pic_url
FROM    performance p
        left outer join singer s on s.performed_by = p.performers
;
