import os
from lxml import etree, objectify
import unittest
import hashlib
import uuid
from mimetypes import MimeTypes
from config.config import root_dir
from subprocess import Popen, PIPE
from earkcore.utils.datetimeutils import current_timestamp, DT_ISO_FMT_SEC_PREC, get_file_ctime_iso_date_str
from earkcore.format.formatidentification import FormatIdentification
from earkcore.metadata.XmlHelper import q, XSI_NS
import fnmatch

METS_NS = 'http://www.loc.gov/METS/'
METSEXT_NS = 'ExtensionMETS'
XLINK_NS = "http://www.w3.org/1999/xlink"
METS_NSMAP = {None: METS_NS, "xlink": "http://www.w3.org/1999/xlink", "ext": METSEXT_NS,
              "xsi": "http://www.w3.org/2001/XMLSchema-instance"}
DELIVERY_METS_NSMAP = {None: METS_NS, "xlink": "http://www.w3.org/1999/xlink",
                       "xsi": "http://www.w3.org/2001/XMLSchema-instance"}

M = objectify.ElementMaker(
    annotate=False,
    namespace=METS_NS,
    nsmap=METS_NSMAP)


class MetsGenerator(object):
    fid = FormatIdentification()
    mime = MimeTypes()
    root_path = ""

    def __init__(self, root_path):
        print "Working in rootdir %s" % root_path
        self.root_path = root_path

    def sha256(self, fname):
        hash = hashlib.sha256()
        with open(fname) as f:
            for chunk in iter(lambda: f.read(4096), ""):
                hash.update(chunk)
        return hash.hexdigest()

    def runCommand(self, program, stdin=PIPE, stdout=PIPE, stderr=PIPE):
        result, res_stdout, res_stderr = None, None, None
        try:
            # quote the executable otherwise we run into troubles
            # when the path contains spaces and additional arguments
            # are presented as well.
            # special: invoking bash as login shell here with
            # an unquoted command does not execute /etc/profile

            print 'Launching: ' + ' '.join(program)
            process = Popen(program, stdin=stdin, stdout=stdout, stderr=stderr, shell=False)

            res_stdout, res_stderr = process.communicate()
            result = process.returncode
            print 'Finished: ' + ' '.join(program)

        except Exception as ex:
            res_stderr = ''.join(str(ex.args))
            result = 1

        if result != 0:
            print 'Command failed:' + ''.join(res_stderr)
            raise Exception('Command failed:' + ''.join(res_stderr))

        return result, res_stdout, res_stderr

    def addFile(self, file_name, mets_filegroup):
        # reload(sys)
        # sys.setdefaultencoding('utf8')
        file_url = "file://./%s" % os.path.relpath(file_name, self.root_path)
        file_mimetype, _ = self.mime.guess_type(file_url)
        file_checksum = self.sha256(file_name)
        file_size = os.path.getsize(file_name)
        file_cdate = get_file_ctime_iso_date_str(file_name, DT_ISO_FMT_SEC_PREC)
        file_id = "ID" + uuid.uuid4().__str__()
        mets_file = M.file(
            {"MIMETYPE": file_mimetype, "CHECKSUMTYPE": "SHA-256", "CREATED": file_cdate, "CHECKSUM": file_checksum,
             "USE": "Datafile", "ID": file_id, "SIZE": file_size})
        mets_filegroup.append(mets_file)
        # _,fname = os.path.split(file_name)
        mets_FLocat = M.FLocat({q(XLINK_NS, 'href'): file_url, "LOCTYPE": "URL", q(XLINK_NS, 'type'): 'simple'})
        mets_file.append(mets_FLocat)
        return file_id

    def addFiles(self, folder, mets_filegroup):
        ids = []
        for top, dirs, files in os.walk(folder):
            for fn in files:
                file_name = os.path.join(top, fn)
                file_id = self.addFile(file_name, mets_filegroup)
                ids.append(file_id)
        return ids

    def make_mdref(self, path, file, id, mdtype):
        mimetype, _ = self.mime.guess_type(os.path.join(path, file))
        rel_path = "file://./%s" % os.path.relpath(os.path.join(path, file), self.root_path)
        mets_mdref = {"LOCTYPE": "URL",
                      "MIMETYPE": mimetype,
                      "CREATED": current_timestamp(),
                      q(XLINK_NS, "type"): "simple",
                      q(XLINK_NS, "href"): rel_path,
                      "CHECKSUMTYPE": "SHA-256",
                      "CHECKSUM": self.sha256(os.path.join(path, file)),
                      "ID": id,
                      "MDTYPE": mdtype}
        return mets_mdref

    def createMets(self, mets_data):
        packageid = mets_data['packageid']
        packagetype = mets_data['type']

        ###########################
        # create METS skeleton
        ###########################

        # create Mets root
        METS_ATTRIBUTES = {"OBJID": packageid,
                           "LABEL": "METS file describing the AIP matching the OBJID.",
                           "PROFILE": "http://www.ra.ee/METS/v01/IP.xml",
                           "TYPE": packagetype}
        root = M.mets(METS_ATTRIBUTES)
        root.attrib['{%s}schemaLocation' % XSI_NS] = "http://www.loc.gov/METS/ schemas/IP.xsd ExtensionMETS schemas/ExtensionMETS.xsd http://www.w3.org/1999/xlink schemas/xlink.xsd"

        # create Mets header
        mets_hdr = M.metsHdr({"CREATEDATE": current_timestamp(), "RECORDSTATUS": "NEW"})
        root.append(mets_hdr)
        mets_hdr.append(M.metsDocumentID("METS.xml"))

        # create dmdSec
        mets_dmd = M.dmdSec({"ID": "ID" + uuid.uuid4().__str__()})
        root.append(mets_dmd)

        # create amdSec
        mets_amdSec = M.amdSec({"ID": "ID" + uuid.uuid4().__str__()})
        root.append(mets_amdSec)

        # create fileSec
        mets_fileSec = M.fileSec()
        root.append(mets_fileSec)

        # general filegroup
        mets_filegroup = M.fileGrp({"ID": "ID" + uuid.uuid4().__str__(), "USE": "general filegroup"})
        mets_fileSec.append(mets_filegroup)

        # structMap and div for the whole package (metadata, schema and /data)
        mets_structmap = M.structMap({"LABEL": "Simple AIP structuring", "TYPE": "logical"})
        root.append(mets_structmap)
        mets_structmap_div = M.div({"LABEL": "Package structure"})
        mets_structmap.append(mets_structmap_div)

        # metadata structmap - IP root level!
        mets_structmap_metadata_div = M.div({"LABEL": "metadata files"})
        mets_structmap_div.append(mets_structmap_metadata_div)

        # structmap for schema files
        mets_structmap_schema_div = M.div({"LABEL": "schema files"})
        mets_structmap_div.append(mets_structmap_schema_div)

        # content structmap - all representations! (is only filled if no separate METS exists for the rep)
        mets_structmap_content_div = M.div({"LABEL": "files from /data"})
        mets_structmap_div.append(mets_structmap_content_div)

        # create structmap and div for Mets files from representations
        mets_structmap_reps = M.structMap({"TYPE": "logical", "LABEL": "representations"})
        root.append(mets_structmap_reps)
        mets_div_reps = M.div({"LABEL": "representations", "TYPE": "type"})
        mets_structmap_reps.append(mets_div_reps)

        ###########################
        # add to Mets skeleton
        ###########################

        # TODO: differentiate between cases (when calling this function) - if needed

        # case 1: create a Mets file for a whole package (SIP or AIP)
        workdir_length = len(self.root_path)
        for directory, subdirectories, filenames in os.walk(self.root_path):
            if directory.endswith('metadata/earkweb'):
                del filenames[:]
                del subdirectories[:]
            if directory.endswith('submission/metadata') or directory.endswith('submission/schemas'):
                del filenames[:]
                del subdirectories[:]
            if directory == os.path.join(self.root_path, 'metadata'):
                # Metadata on IP root level - if there are folders for representation-specific metadata,
                # check if the corresponding representation has a Mets file. If yes, skip; if no, add to IP root Mets.
                for filename in filenames:
                    if filename == 'earkweb.log':
                        mets_digiprovmd = M.digiprovMD({"ID": "ID" + uuid.uuid4().__str__()})
                        mets_amdSec.append(mets_digiprovmd)
                        id = "ID" + uuid.uuid4().__str__()
                        ref = self.make_mdref(directory, filename, id, 'OTHER')
                        mets_mdref = M.mdRef(ref)
                        mets_digiprovmd.append(mets_mdref)
                        fptr = M.fptr({"FILEID": id})
                        mets_structmap_metadata_div.append(fptr)
                del subdirectories[:]  # prevent loop to iterate subfolders outside of this if statement
                dirlist = os.listdir(os.path.join(self.root_path, 'metadata'))
                for dirname in dirlist:
                    if fnmatch.fnmatch(dirname, '*_mig-*'):
                        # TODO: maybe list it all the time?
                        # this folder contains metadata for a representation/migration, currently:
                        # only listed if no representation Mets file exists
                        if os.path.isfile(os.path.join(self.root_path, 'representations/%s/METS.xml') % dirname):
                            pass
                        else:
                            for dir, subdir, files in os.walk(os.path.join(self.root_path, 'metadata/%s') % dirname):
                                for filename in files:
                                    if dir.endswith('descriptive'):
                                        id = "ID" + uuid.uuid4().__str__()
                                        ref = self.make_mdref(directory, filename, id, 'OTHER')
                                        mets_mdref = M.mdRef(ref)
                                        mets_dmd.append(mets_mdref)
                                        fptr = M.fptr({"FILEID": id})
                                        mets_structmap_metadata_div.append(fptr)
                                    elif dir.endswith('preservation'):
                                        # TODO: find correct location in the Mets document
                                        mets_digiprovmd = M.digiprovMD({"ID": "ID" + uuid.uuid4().__str__()})
                                        mets_amdSec.append(mets_digiprovmd)
                                        id = "ID" + uuid.uuid4().__str__()
                                        mdtype = ''
                                        if filename.startswith('premis') or filename.endswith('premis.xml'):
                                            mdtype = 'PREMIS'
                                        else:
                                            mdtype = 'OTHER'
                                        ref = self.make_mdref(directory, filename, id, mdtype)
                                        mets_mdref = M.mdRef(ref)
                                        mets_digiprovmd.append(mets_mdref)
                                        fptr = M.fptr({"FILEID": id})
                                        mets_structmap_metadata_div.append(fptr)
                                    elif filename:
                                        print 'Unclassified metadata file %s in %s.' % (filename, dir)
                    elif dirname:
                        # metadata that should be listed in the Mets
                        for dir, subdir, files in os.walk(os.path.join(self.root_path, 'metadata/%s') % dirname):
                            for filename in files:
                                if dir.endswith('descriptive'):
                                    id = "ID" + uuid.uuid4().__str__()
                                    # TODO: change MDTYPE
                                    ref = self.make_mdref(directory, filename, id, 'OTHER')
                                    mets_mdref = M.mdRef(ref)
                                    mets_dmd.append(mets_mdref)
                                    fptr = M.fptr({"FILEID": id})
                                    mets_structmap_metadata_div.append(fptr)
                                elif dir.endswith('preservation'):
                                    mets_digiprovmd = M.digiprovMD({"ID": "ID" + uuid.uuid4().__str__()})
                                    mets_amdSec.append(mets_digiprovmd)
                                    id = "ID" + uuid.uuid4().__str__()
                                    mdtype = ''
                                    if filename.startswith('premis') or filename.endswith('premis.xml'):
                                        mdtype = 'PREMIS'
                                    elif filename:
                                        mdtype = 'OTHER'
                                    ref = self.make_mdref(directory, filename, id, mdtype)
                                    mets_mdref = M.mdRef(ref)
                                    mets_digiprovmd.append(mets_mdref)
                                    fptr = M.fptr({"FILEID": id})
                                    mets_structmap_metadata_div.append(fptr)
                                elif filename:
                                    print 'Unclassified metadata file %s in %s.' % (filename, dir)
            else:
                # Any other folder outside of /<root>/metadata
                for filename in filenames:
                    if directory == self.root_path:
                        # ignore files on IP root level
                        del filename
                    else:
                        # TODO: list rep metadata only in the rep Mets?
                        rel_path_file = ('file://.' + directory[workdir_length:] + '/' + filename).decode('utf-8')
                        if filename.lower() == 'mets.xml':
                            # delete the subdirectories list to stop os.walk from traversing further;
                            # mets file should be added as <mets:mptr> to <structMap> for corresponding rep
                            del subdirectories[:]
                            rep_name = directory.rsplit('/', 1)[1]
                            # create structMap div and append to representations structMap
                            mets_structmap_rep_div = M.div(
                                {"LABEL": rep_name, "TYPE": "representation mets", "ID": "ID" + uuid.uuid4().__str__()})
                            mets_div_reps.append(mets_structmap_rep_div)
                            # add mets file as <mets:mptr>
                            metspointer = M.mptr({"LOCTYPE": "URL",
                                                  q(XLINK_NS, "title"): "mets file describing representation: " + rep_name + " of AIP: " + packageid,
                                                  q(XLINK_NS, "href"): rel_path_file,
                                                  "ID": "ID" + uuid.uuid4().__str__()})
                            mets_structmap_rep_div.append(metspointer)
                            # also add the rep mets to the filegroup, so we can have a fptr
                            id = self.addFile(os.path.join(directory, filename), mets_filegroup)
                            mets_fptr = M.fptr({"FILEID": id})
                            mets_structmap_rep_div.append(mets_fptr)
                        elif filename and directory.endswith('schemas'):
                            # schema files
                            id = self.addFile(os.path.join(directory, filename), mets_filegroup)
                            fptr = M.fptr({'FILEID': id})
                            mets_structmap_schema_div.append(fptr)
                        elif filename:
                            id = self.addFile(os.path.join(directory, filename), mets_filegroup)
                            fptr = M.fptr({"FILEID": id})
                            mets_structmap_content_div.append(fptr)

        str = etree.tostring(root, encoding='UTF-8', pretty_print=True, xml_declaration=True)

        path_mets = os.path.join(self.root_path, 'METS.xml')
        with open(path_mets, 'w') as output_file:
            output_file.write(str)


class testMetsCreation(unittest.TestCase):
    def testCreateMets(self):
        metsgen = MetsGenerator(os.path.join("/var/data/earkweb/work/bbfc7446-d2af-4ab9-8479-692c270989bb"))
        mets_data = {'packageid': '996ed635-3e13-4ee5-8e5b-e9661e1d9a93',
                     'type': 'AIP'}
        metsgen.createMets(mets_data)


if __name__ == '__main__':
    unittest.main()
