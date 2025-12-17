from flask import Flask, render_template, request, jsonify, send_file, url_for
import sqlite3
from datetime import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration for file uploads
UPLOAD_FOLDER = '/home/LMN/uploads'
# Extended file types including coding files
ALLOWED_EXTENSIONS = {
    # Text and Documents
    'txt', 'pdf', 'doc', 'docx', 'rtf', 'odt',
    # Images
    'png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg',
    # Coding Files
    'py', 'js', 'html', 'css', 'cpp', 'c', 'h', 'java', 'cs',
    'php', 'rb', 'swift', 'kt', 'go', 'rs', 'sql', 'sh',
    # Web Development
    'json', 'xml', 'yaml', 'yml', 'md', 'jsx', 'tsx', 'vue',
    # Archives
    'zip', 'rar', '7z', 'tar', 'gz',
    # Data Files
    'csv', 'xlsx', 'xls', 'db', 'sqlite'
}

# Maximum file size (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create uploads directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# File type categories for better organization
FILE_CATEGORIES = {
    'code': {'py', 'js', 'html', 'css', 'cpp', 'c', 'h', 'java', 'cs', 'php', 'rb', 'swift', 'kt', 'go', 'rs'},
    'document': {'txt', 'pdf', 'doc', 'docx', 'rtf', 'odt', 'md'},
    'image': {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg'},
    'web': {'json', 'xml', 'yaml', 'yml', 'jsx', 'tsx', 'vue'},
    'archive': {'zip', 'rar', '7z', 'tar', 'gz'},
    'data': {'csv', 'xlsx', 'xls', 'db', 'sqlite'}
}

def convert_str_to_datetime(date_str):
    """Convert string to datetime object if it's a string"""
    if isinstance(date_str, str):
        try:
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return datetime.now()  # Fallback to current time if parsing fails
    return date_str  # Return as is if already datetime object

# Database setup and helper functions
def init_db():
    try:
        conn = sqlite3.connect('notebook.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS notes
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      content TEXT,
                      page_type TEXT,
                      last_updated TIMESTAMP)''')

        c.execute('''CREATE TABLE IF NOT EXISTS files
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      filename TEXT,
                      file_path TEXT,
                      upload_date TIMESTAMP,
                      file_type TEXT,
                      file_category TEXT,
                      file_size INTEGER)''')
        conn.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise
    finally:
        conn.close()

# Initialize database
init_db()

def get_db_connection():
    return sqlite3.connect('notebook.db')

def get_file_category(file_type):
    for category, extensions in FILE_CATEGORIES.items():
        if file_type in extensions:
            return category
    return 'other'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size(file_path):
    return os.path.getsize(file_path)

# Note functions
def save_note(content, page_type):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        c.execute('''UPDATE notes 
                     SET content = ?, last_updated = ? 
                     WHERE page_type = ?''',
                  (content, current_time, page_type))

        if c.rowcount == 0:
            c.execute('''INSERT INTO notes (content, page_type, last_updated)
                         VALUES (?, ?, ?)''',
                      (content, page_type, current_time))

        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving note: {e}")
        return False
    finally:
        conn.close()

def get_note(page_type):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT content FROM notes WHERE page_type = ? ORDER BY last_updated DESC LIMIT 1', (page_type,))
        result = c.fetchone()
        return result[0] if result else ""
    except Exception as e:
        print(f"Error getting note: {e}")
        return ""
    finally:
        conn.close()

# File functions
def get_all_files():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''SELECT id, filename, upload_date, file_type, file_category, file_size 
                     FROM files ORDER BY upload_date DESC''')
        files = c.fetchall()
        # Convert to list so we can modify the tuple
        files = [list(file) for file in files]
        # Convert upload_date string to datetime object
        for file in files:
            file[2] = convert_str_to_datetime(file[2])
        return files
    except Exception as e:
        print(f"Error getting files: {e}")
        return []
    finally:
        conn.close()

def get_files_by_category(category):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''SELECT id, filename, upload_date, file_type, file_size 
                     FROM files WHERE file_category = ? 
                     ORDER BY upload_date DESC''', (category,))
        files = c.fetchall()
        # Convert to list so we can modify the tuple
        files = [list(file) for file in files]
        # Convert upload_date string to datetime object
        for file in files:
            file[2] = convert_str_to_datetime(file[2])
        return files
    except Exception as e:
        print(f"Error getting files by category: {e}")
        return []
    finally:
        conn.close()

def save_file_to_db(filename, file_path, file_type):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        file_size = get_file_size(file_path)
        file_category = get_file_category(file_type)
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        c.execute('''INSERT INTO files (filename, file_path, upload_date, file_type, file_category, file_size)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (filename, file_path, current_time, file_type, file_category, file_size))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving file to database: {e}")
        return False
    finally:
        conn.close()

def delete_file(file_id):
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # First get the file path
        c.execute('SELECT file_path FROM files WHERE id = ?', (file_id,))
        result = c.fetchone()

        if result:
            file_path = result[0]
            # Delete the physical file
            if os.path.exists(file_path):
                os.remove(file_path)

            # Delete the database entry
            c.execute('DELETE FROM files WHERE id = ?', (file_id,))
            conn.commit()
            return True
        return False
    except Exception as e:
        print(f"Error deleting file: {e}")
        return False
    finally:
        conn.close()

def delete_all_files():
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Get all file paths
        c.execute('SELECT file_path FROM files')
        files = c.fetchall()

        # Delete all physical files
        for file_path, in files:
            if os.path.exists(file_path):
                os.remove(file_path)

        # Clear the files table
        c.execute('DELETE FROM files')
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting all files: {e}")
        return False
    finally:
        conn.close()

def clear_database():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('DELETE FROM notes')
        conn.commit()
        return True
    except Exception as e:
        print(f"Error clearing database: {e}")
        return False
    finally:
        conn.close()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/notes')
def notes():
    content = get_note('notes')
    return render_template('realtime.html', content=content)

@app.route('/files')
def files():
    category = request.args.get('category', None)
    if category and category in FILE_CATEGORIES:
        files = get_files_by_category(category)
    else:
        files = get_all_files()
    return render_template('files.html', files=files, categories=FILE_CATEGORIES.keys())

@app.route('/save_note', methods=['POST'])
def save_notes():
    content = request.form.get('content', '')
    if save_note(content, 'notes'):
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Failed to save note'}), 500

@app.route('/upload_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Check if file already exists, append number if it does
        base, extension = os.path.splitext(filename)
        counter = 1
        while os.path.exists(file_path):
            filename = f"{base}_{counter}{extension}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            counter += 1

        try:
            file.save(file_path)
            file_type = filename.rsplit('.', 1)[1].lower()

            if save_file_to_db(filename, file_path, file_type):
                return jsonify({
                    'status': 'success',
                    'message': 'File uploaded successfully',
                    'filename': filename
                })
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    return jsonify({'status': 'error', 'message': 'Invalid file type'}), 400

@app.route('/download_file/<int:file_id>')
def download_file(file_id):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT filename, file_path FROM files WHERE id = ?', (file_id,))
        result = c.fetchone()

        if result:
            filename, file_path = result
            if os.path.exists(file_path):
                return send_file(file_path, as_attachment=True, download_name=filename)
            return jsonify({'status': 'error', 'message': 'File not found on server'}), 404

        return jsonify({'status': 'error', 'message': 'File not found in database'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/clear_database', methods=['POST'])
def clear_db():
    try:
        if clear_database():
            return jsonify({'status': 'success'})
        return jsonify({'status': 'error', 'message': 'Failed to clear database'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/delete_file/<int:file_id>', methods=['DELETE'])
def delete_file_route(file_id):
    if delete_file(file_id):
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Failed to delete file'}), 500

@app.route('/delete_all_files', methods=['DELETE'])
def delete_all_files_route():
    if delete_all_files():
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Failed to delete all files'}), 500

if __name__ == '__main__':
    app.run(debug=True)