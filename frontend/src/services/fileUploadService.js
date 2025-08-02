import supabaseAuthService from './supabaseAuthService';

class FileUploadService {
  constructor() {
    this.bucketName = 'customer-documents';
  }

  // Get the current supabase client with authentication
  getSupabaseClient() {
    return supabaseAuthService.getClient();
  }

  // Upload file to Supabase Storage with custom JWT token
  async uploadFile(file, customerId, tenantId) {
    try {
      console.log('Uploading file to Supabase:', file.name, 'for customer:', customerId);
      
      // Get JWT token from localStorage
      const token = localStorage.getItem('accessToken');
      if (!token) {
        throw new Error('No authentication token found');
      }
      
      // Create a new Supabase client with our custom JWT token
      const { createClient } = await import('@supabase/supabase-js');
      const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
      const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;
      
      const supabaseWithAuth = createClient(supabaseUrl, supabaseAnonKey, {
        global: {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      });
      
      // Create a unique file name
      const fileExt = file.name.split('.').pop();
      const fileName = `${tenantId}/${customerId}/incorporation_doc_${Date.now()}.${fileExt}`;

      console.log('Uploading file:', fileName, 'to bucket:', this.bucketName);

      // Upload file to Supabase Storage
      const { data, error } = await supabaseWithAuth.storage
        .from(this.bucketName)
        .upload(fileName, file, {
          cacheControl: '3600',
          upsert: false
        });

      if (error) {
        console.error('Supabase storage upload error:', error);
        throw error;
      }

      console.log('File uploaded successfully:', data);

      // Get the public URL
      const { data: { publicUrl } } = supabaseWithAuth.storage
        .from(this.bucketName)
        .getPublicUrl(fileName);

      return {
        success: true,
        path: data.path,
        publicUrl: publicUrl
      };
    } catch (error) {
      console.error('File upload error:', error);
      return {
        success: false,
        error: error.message || 'File upload failed'
      };
    }
  }

  // Download file from Supabase Storage with custom JWT token
  async downloadFile(filePath) {
    try {
      console.log('Downloading file with custom JWT:', filePath);
      
      // Get JWT token from localStorage
      const token = localStorage.getItem('accessToken');
      if (!token) {
        throw new Error('No authentication token found');
      }
      
      // Create a new Supabase client with our custom JWT token
      const { createClient } = await import('@supabase/supabase-js');
      const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
      const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;
      
      const supabaseWithAuth = createClient(supabaseUrl, supabaseAnonKey, {
        global: {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      });
      
      const { data, error } = await supabaseWithAuth.storage
        .from(this.bucketName)
        .download(filePath);

      if (error) {
        console.error('Supabase download error:', error);
        throw error;
      }

      console.log('File downloaded successfully, size:', data?.size || 'unknown');

      return {
        success: true,
        data: data
      };
    } catch (error) {
      console.error('File download error:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Move file from temp path to real customer path
  async moveFile(oldPath, realCustomerId, tenantId) {
    try {
      console.log('=== FILE MOVE PROCESS START ===');
      console.log('Moving file from:', oldPath, 'to customer:', realCustomerId, 'tenant:', tenantId);
      
      // Get JWT token from localStorage
      const token = localStorage.getItem('accessToken');
      if (!token) {
        throw new Error('No authentication token found');
      }
      console.log('JWT token found, length:', token.length);
      
      // Create a new Supabase client with our custom JWT token
      const { createClient } = await import('@supabase/supabase-js');
      const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
      const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;
      
      console.log('Supabase URL:', supabaseUrl);
      console.log('Supabase Anon Key length:', supabaseAnonKey?.length || 0);
      
      const supabaseWithAuth = createClient(supabaseUrl, supabaseAnonKey, {
        global: {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      });
      
      console.log('Supabase client created with auth headers');
      
      // Download the file from old path
      console.log('Attempting to download file from:', oldPath);
      const { data: fileData, error: downloadError } = await supabaseWithAuth.storage
        .from(this.bucketName)
        .download(oldPath);
      
      if (downloadError) {
        console.error('Error downloading file for move:', downloadError);
        throw downloadError;
      }
      
      console.log('File downloaded successfully, size:', fileData?.size || 'unknown');
      
      // Create new path with real customer ID
      const fileExt = oldPath.split('.').pop();
      const newPath = `${tenantId}/${realCustomerId}/incorporation_doc_${Date.now()}.${fileExt}`;
      
      console.log('Uploading file to new path:', newPath);
      
      // Upload to new path
      const { data: uploadData, error: uploadError } = await supabaseWithAuth.storage
        .from(this.bucketName)
        .upload(newPath, fileData, {
          cacheControl: '3600',
          upsert: false
        });
      
      if (uploadError) {
        console.error('Error uploading file to new path:', uploadError);
        throw uploadError;
      }
      
      console.log('File uploaded to new path successfully:', uploadData);
      
      // Delete the old file
      console.log('Attempting to delete old file:', oldPath);
      const { error: deleteError } = await supabaseWithAuth.storage
        .from(this.bucketName)
        .remove([oldPath]);
      
      if (deleteError) {
        console.warn('Warning: Could not delete old file:', deleteError);
        // Don't throw error here as the move was successful
      } else {
        console.log('Old file deleted successfully');
      }
      
      console.log('=== FILE MOVE PROCESS COMPLETE ===');
      console.log('File moved successfully from', oldPath, 'to', newPath);
      
      return {
        success: true,
        path: newPath
      };
    } catch (error) {
      console.error('=== FILE MOVE PROCESS FAILED ===');
      console.error('File move error:', error);
      console.error('Error details:', {
        message: error.message,
        name: error.name,
        stack: error.stack
      });
      return {
        success: false,
        error: error.message || 'File move failed'
      };
    }
  }

  // Download file as blob to force download instead of opening in browser
  async downloadFileAsBlob(filePath) {
    try {
      console.log('Downloading file as blob with custom JWT:', filePath);
      
      // Get JWT token from localStorage
      const token = localStorage.getItem('accessToken');
      if (!token) {
        throw new Error('No authentication token found');
      }
      
      // Create a new Supabase client with our custom JWT token
      const { createClient } = await import('@supabase/supabase-js');
      const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
      const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;
      
      const supabaseWithAuth = createClient(supabaseUrl, supabaseAnonKey, {
        global: {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      });
      
      // Download the file as a blob
      const { data, error } = await supabaseWithAuth.storage
        .from(this.bucketName)
        .download(filePath);

      if (error) {
        console.error('File download error:', error);
        throw error;
      }

      console.log('File downloaded as blob successfully, size:', data?.size || 'unknown');

      // Create a blob URL and trigger download
      const url = URL.createObjectURL(data);
      const link = document.createElement('a');
      link.href = url;
      
      // Extract filename from path
      const fileName = filePath.split('/').pop() || 'document.pdf';
      link.download = fileName;
      
      // Add to DOM, click, and remove
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // Clean up the blob URL
      URL.revokeObjectURL(url);

      return {
        success: true,
        message: 'File downloaded successfully'
      };
    } catch (error) {
      console.error('File download error:', error);
      return {
        success: false,
        error: error.message || 'Download failed'
      };
    }
  }

  // Get signed URL for private file access
  async getSignedUrl(filePath, expiresIn = 3600) {
    try {
      console.log('Getting signed URL with custom JWT:', filePath);
      
      // Get JWT token from localStorage
      const token = localStorage.getItem('accessToken');
      if (!token) {
        throw new Error('No authentication token found');
      }
      
      // Create a new Supabase client with our custom JWT token
      const { createClient } = await import('@supabase/supabase-js');
      const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
      const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;
      
      const supabaseWithAuth = createClient(supabaseUrl, supabaseAnonKey, {
        global: {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      });
      
      const { data, error } = await supabaseWithAuth.storage
        .from(this.bucketName)
        .createSignedUrl(filePath, expiresIn);

      if (error) {
        console.error('Supabase signed URL error:', error);
        throw error;
      }

      console.log('Signed URL created successfully');

      return {
        success: true,
        signedUrl: data.signedUrl
      };
    } catch (error) {
      console.error('Get signed URL error:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Delete file from Supabase Storage
  async deleteFile(filePath) {
    try {
      const supabase = this.getSupabaseClient();
      
      const { error } = await supabase.storage
        .from(this.bucketName)
        .remove([filePath]);

      if (error) throw error;

      return {
        success: true
      };
    } catch (error) {
      console.error('File delete error:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Validate file type and size
  validateFile(file) {
    const allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'image/jpeg',
      'image/png'
    ];

    const maxSize = 10 * 1024 * 1024; // 10MB

    if (!allowedTypes.includes(file.type)) {
      return {
        valid: false,
        error: 'Invalid file type. Please upload PDF, Word documents, or images (JPEG/PNG).'
      };
    }

    if (file.size > maxSize) {
      return {
        valid: false,
        error: 'File size exceeds 10MB limit.'
      };
    }

    return {
      valid: true
    };
  }

  // Get a download URL that forces download instead of opening in browser
  async getDownloadUrl(filePath) {
    try {
      console.log('Getting download URL with custom JWT:', filePath);
      
      // Get JWT token from localStorage
      const token = localStorage.getItem('accessToken');
      if (!token) {
        throw new Error('No authentication token found');
      }
      
      // Create a new Supabase client with our custom JWT token
      const { createClient } = await import('@supabase/supabase-js');
      const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
      const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;
      
      const supabaseWithAuth = createClient(supabaseUrl, supabaseAnonKey, {
        global: {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      });
      
      // Get a signed URL with a download parameter
      const { data, error } = await supabaseWithAuth.storage
        .from(this.bucketName)
        .createSignedUrl(filePath, 3600, {
          download: true
        });

      if (error) {
        console.error('Supabase download URL error:', error);
        throw error;
      }

      console.log('Download URL created successfully');

      return {
        success: true,
        downloadUrl: data.signedUrl
      };
    } catch (error) {
      console.error('Get download URL error:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }
}

export default new FileUploadService();