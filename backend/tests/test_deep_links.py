import unittest
from app.onenote.link_builder import (
    is_real_onenote_object_id,
    is_real_graph_id,
    format_object_id_for_onenote,
    format_id_param,
    build_object_client_url,
    get_exact_image_hyperlinks,
)

class TestOneNoteDeepLinks(unittest.TestCase):
    def test_expected_user_example(self):
        """Tests the exact canonical URL from the user's requirement prompt."""
        cid = "b6ecec459b998637"
        url = build_object_client_url(
            notebook_name="My Notebook",
            section_name="Quick Notes",
            page_title="Difference between Git and GitHub",
            section_id="a2760d1e-79bd-48ac-85fd-3f084ee70322",
            page_id="7bd5e942-9e4d-466c-87a5-025e3479e304",
            object_id="{4cdb24f8-79bd-48ac-85fd-3f084ee70322}{207}",
            cid=cid,
        )
        expected = (
            "onenote:https://d.docs.live.net/b6ecec459b998637/OneNote%20Notebooks/My%20Notebook/Quick%20Notes.one#"
            "Difference%20between%20Git%20and%20GitHub"
            "&section-id={a2760d1e-79bd-48ac-85fd-3f084ee70322}"
            "&page-id={7bd5e942-9e4d-466c-87a5-025e3479e304}"
            "&object-id={4cdb24f8-79bd-48ac-85fd-3f084ee70322}{207}"
            "&end"
        )
        self.assertEqual(url, expected)

    def test_from_graph_base_client_url(self):
        """Tests taking Graph API's native oneNoteClientUrl and injecting the exact object ID."""
        graph_base = (
            "onenote:https://d.docs.live.net/b6ecec459b998637/OneNote%20Notebooks/My%20Notebook/Quick%20Notes.one#"
            "Difference%20between%20Git%20and%20GitHub"
            "&section-id=a2760d1e-79bd-48ac-85fd-3f084ee70322"
            "&page-id=7bd5e942-9e4d-466c-87a5-025e3479e304"
            "&end"
        )
        url = build_object_client_url(
            base_client_url=graph_base,
            object_id="img:{4cdb24f8-79bd-48ac-85fd-3f084ee70322}{207}",
            cid="b6ecec459b998637",
        )
        expected = (
            "onenote:https://d.docs.live.net/b6ecec459b998637/OneNote%20Notebooks/My%20Notebook/Quick%20Notes.one#"
            "Difference%20between%20Git%20and%20GitHub"
            "&section-id={a2760d1e-79bd-48ac-85fd-3f084ee70322}"
            "&page-id={7bd5e942-9e4d-466c-87a5-025e3479e304}"
            "&object-id={4cdb24f8-79bd-48ac-85fd-3f084ee70322}{207}"
            "&end"
        )
        self.assertEqual(url, expected)

    def test_multiple_images_on_same_page(self):
        """Tests that two different images on the same page produce distinct object IDs."""
        graph_base = (
            "onenote:https://d.docs.live.net/b6ecec459b998637/OneNote%20Notebooks/My%20Notebook/Quick%20Notes.one#"
            "Difference%20between%20Git%20and%20GitHub"
            "&section-id=a2760d1e-79bd-48ac-85fd-3f084ee70322"
            "&page-id=7bd5e942-9e4d-466c-87a5-025e3479e304"
            "&end"
        )
        url1 = build_object_client_url(
            base_client_url=graph_base,
            object_id="{4cdb24f8-79bd-48ac-85fd-3f084ee70322}{100}",
            cid="b6ecec459b998637",
        )
        url2 = build_object_client_url(
            base_client_url=graph_base,
            object_id="{4cdb24f8-79bd-48ac-85fd-3f084ee70322}{207}",
            cid="b6ecec459b998637",
        )
        self.assertIn("object-id={4cdb24f8-79bd-48ac-85fd-3f084ee70322}{100}", url1)
        self.assertIn("object-id={4cdb24f8-79bd-48ac-85fd-3f084ee70322}{207}", url2)
        self.assertNotEqual(url1, url2)

    def test_reject_synthetic_ids(self):
        """Strictly rejects synthetic object IDs like img-obj-F4E962 and returns None."""
        self.assertFalse(is_real_onenote_object_id("img-obj-F4E962"))
        self.assertFalse(is_real_onenote_object_id("res_1"))
        self.assertFalse(is_real_onenote_object_id("ONENOTE-b6ecec-09A397"))
        url = build_object_client_url(
            notebook_name="My Notebook",
            section_name="New Section 2",
            page_title="Saree designs",
            section_id="b6ecec45-9b99-8637-0002-000000000002",
            page_id="0-b6ecec-p-saree-designs",
            object_id="img-obj-F4E962",
        )
        self.assertIsNone(url)

    def test_reject_page_title_only_links(self):
        """Ensures bare .one#title links without section/page/object IDs are never constructed."""
        malformed = "onenote:https://d.docs.live.net/b6ecec459b998637/OneNote Notebooks/My Notebook/New Section 2.one#Saree designs"
        res = get_exact_image_hyperlinks({
            "notebook_name": "My Notebook",
            "section_name": "New Section 2",
            "page_title": "Saree designs",
            "onenote_client_url": malformed,
            "onenote_web_url": "https://onedrive.live.com/redir.aspx?cid=b6ecec459b998637&page=edit",
        })
        # client_url MUST fall back to the official page-level web URL (https://...)
        self.assertTrue(res["client_url"].startswith("https://"))
        self.assertIsNone(res["object_client_url"])

if __name__ == "__main__":
    unittest.main()
